import os
import torch
import torch.nn.functional as F
import gc
from tqdm import tqdm
from rich.console import Console

console = Console()

# =========================================================
# 🔹 TOKENIZER
# =========================================================
def load_tokenizer(args):
    import json
    from utils import HybridTokenizer, SyllableTokenizer, BpeTokenizer

    console.print("[cyan]Cargando tokenizer...[/cyan]")
    with open(args.vocab_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    vocab = {v: int(k) for k, v in data["indexed"].items()} if "indexed" in data else {tok: i for i, tok in enumerate(data["vocab"])}
    
    syllable = SyllableTokenizer()
    syllable.load_vocab(args.vocab_path)

    merges = []
    if getattr(args, "merges_path", None) and os.path.exists(args.merges_path):
        with open(args.merges_path, "r", encoding="utf-8") as f:
            merges = json.load(f)

    bpe = BpeTokenizer(merges)
    return HybridTokenizer(syllable, bpe, vocab)

# =========================================================
# 🔹 MEMORY INJECTION (Optimizado)
# =========================================================
def inject_memory_into_batch(x, tokenizer, memory_manager, device, block_size):
    # Solo decodificamos el primer ejemplo para ahorrar CPU
    query_text = tokenizer.decode(x[0].tolist())
    memories = memory_manager.retrieve(query=query_text, top_k=3)
    selected = memory_manager.evaluate(memories)

    if not selected:
        return x, []

    memory_text = " ".join([f"[MEM] {m}" for m in selected])
    mem_tokens = tokenizer.encode(memory_text)
    
    mem_tensor = torch.tensor(mem_tokens, dtype=torch.long, device=device).unsqueeze(0)
    mem_tensor = mem_tensor.expand(x.size(0), -1) # expand es más eficiente que repeat (no duplica RAM)

    x = torch.cat([mem_tensor, x], dim=1)
    return x[:, -block_size:], memories

# =========================================================
# 🔹 TRAIN EPOCH (Turbo Optimized)
# =========================================================
def train_epoch(model, loader, optimizer, device, memory_manager, tokenizer, block_size, sampler, scheduler, source_map, accumulation_steps=4):
    model.train()
    total_loss = 0
    scaler = torch.amp.GradScaler(device.type, enabled=(device.type == "cuda"))
    pbar = tqdm(loader, desc="TRAIN")

    optimizer.zero_grad(set_to_none=True) # set_to_none ahorra un poco más de RAM que zero_grad()

    for step, (x, y) in enumerate(pbar):
        # 🔥 Curriculum dinámico
        if scheduler:
            config = scheduler.get()
            weights = {source_map[name]: w for name, w in config["mix"].items()}
            sampler.set_weights(weights)

        x, y = x.to(device), y.to(device)
        x, memories = inject_memory_into_batch(x, tokenizer, memory_manager, device, block_size)

        # Autocast para Mixed Precision (Ahorro de VRAM/RAM)
        with torch.amp.autocast(device_type=device.type, enabled=True):
            logits = model(x)
            logits = logits.transpose(1, 2)
            
            # Normalizamos la pérdida por los pasos de acumulación
            loss = F.cross_entropy(logits, y, ignore_index=-100)
            loss = loss / accumulation_steps 

            # 🔥 Memory Loss (Refuerzo de contexto)
            if memories:
                try:
                    # Cálculo simplificado para no saturar memoria
                    query_emb = memory_manager._encode_text(tokenizer.decode(x[0, :20].tolist()))
                    sim_bonus = sum(F.cosine_similarity(query_emb, m.embedding, dim=0) for m in memories if m.embedding is not None)
                    if sim_bonus > 0:
                        loss -= (0.02 * (sim_bonus / len(memories))) / accumulation_steps
                except: pass

        # Backward con escalado
        scaler.scale(loss).backward()

        # 🔥 Solo actualizamos pesos cada 'accumulation_steps'
        if (step + 1) % accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            
            # Limpieza agresiva de caché en cada paso de optimización
            if step % 100 == 0:
                gc.collect()
                if device.type == "cuda": torch.cuda.empty_cache()

        total_loss += loss.item() * accumulation_steps
        pbar.set_postfix(loss=loss.item() * accumulation_steps)

        # Mantenimiento de Memoria
        if step % 200 == 0: memory_manager.decay_memory()
        if step % 500 == 0: memory_manager.compress_memory()

    return total_loss / max(1, len(loader))

# =========================================================
# 🔹 RUN TRAINING
# =========================================================
def run_training(args):
    from loaders.bin_dataset import build_dataloaders
    from models import AssistantModel
    from monrix import MemoryManager

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = load_tokenizer(args)
    
    # 🔹 DataLoader optimizado: pin_memory ayuda a transferir datos a la GPU más rápido
    train_loader, val_loader, sampler, source_map = build_dataloaders(
        args, tokenizer, device
    )

    model = AssistantModel(
        vocab_size=len(tokenizer.token_to_id),
        block_size=args.block_size
    ).to(device)

    # Optimizador con Weight Decay para mejor generalización
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)
    scheduler_lr = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.max_iters)

    memory_manager = MemoryManager(tokenizer=tokenizer, model=model, device=device)
    
    curriculum_scheduler = None
    if hasattr(args, "curriculum"):
        from loaders import CurriculumScheduler
        curriculum_scheduler = CurriculumScheduler(args.curriculum)

    os.makedirs("checkpoints", exist_ok=True)
    best_val = float("inf")

    for epoch in range(args.max_iters):
        # Pasamos accumulation_steps=4 (puedes subirlo si tienes MUY poca RAM)
        train_loss = train_epoch(
            model, train_loader, optimizer, device, memory_manager, 
            tokenizer, args.block_size, sampler, curriculum_scheduler, source_map,
            accumulation_steps=4 
        )

        # Evaluación simple (sin gradientes)
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for vx, vy in val_loader:
                vx, vy = vx.to(device), vy.to(device)
                v_logits = model(vx).transpose(1, 2)
                val_loss += F.cross_entropy(v_logits, vy, ignore_index=-100).item()
        val_loss /= max(1, len(val_loader))

        scheduler_lr.step()
        console.print(f"[bold]Epoch {epoch+1}[/bold] | Loss: {train_loss:.4f} | Val: {val_loss:.4f}")

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), "checkpoints/best.pt")
            
    console.print("[green]¡Entrenamiento Synapxion finalizado![/green]")