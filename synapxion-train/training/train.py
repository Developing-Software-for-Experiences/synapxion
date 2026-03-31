# training/train.py
import os
import json
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm

from rich.console import Console
console = Console()

# -------------------------
# 🔹 MODEL FACTORY
# -------------------------
def get_model(name, config):
    if name == "base":
        from models.gptMini import GPTMini
        return GPTMini(**config)

    elif name == "small":
        from models.gptMini import GPTMini
        config["d_model"] = 64
        config["nhead"] = 2
        config["num_layers"] = 2
        return GPTMini(**config)

    else:
        raise ValueError(f"Modelo no reconocido: {name}")

# -------------------------
# 🔹 DATASET FACTORY
# -------------------------
def get_dataset(args, tokenizer):
    if getattr(args, "use_bin", False):
        from utils.bin_dataset import BinDataset

        console.print("[cyan]Usando dataset binario[/cyan]")

        return BinDataset(
            args.bin_path,
            args.idx_path,
            block_size=args.block_size
        )

    else:
        from utils.bin_dataset import TextDataset

        console.print("[yellow]Usando dataset en texto (más lento)[/yellow]")

        text = args.text
        return TextDataset(text, tokenizer, block_size=args.block_size)

# -------------------------
# 🔹 TRAIN LOOP
# -------------------------
def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0

    for x, y in loader:
        x, y = x.to(device), y.to(device)

        optimizer.zero_grad()

        logits = model(x)

        loss = F.cross_entropy(
            logits.view(-1, logits.size(-1)),
            y.view(-1)
        )

        loss.backward()

        # 🔥 evita explosión de gradientes
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        optimizer.step()

        total_loss += loss.item()

    return total_loss / max(1, len(loader))


def eval_epoch(model, loader, device):
    model.eval()
    total_loss = 0.0

    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)

            logits = model(x)

            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                y.view(-1)
            )

            total_loss += loss.item()

    return total_loss / max(1, len(loader))

# -------------------------
# 🔹 MAIN TRAINING
# -------------------------
def run_training(args):

    # -------- Defaults --------
    args.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    args.model_name = getattr(args, "model_name", "base")
    args.batch_size = getattr(args, "batch_size", 8)
    args.block_size = getattr(args, "block_size", 128)
    args.learning_rate = getattr(args, "learning_rate", 3e-4)
    args.max_iters = getattr(args, "max_iters", 10)
    args.patience = getattr(args, "patience", 3)

    console.print(f"[green]Usando device:[/green] {args.device}")

    # -------- Tokenizer --------
    from utils.tokenizer import SyllableTokenizer

    tokenizer = SyllableTokenizer()

    if getattr(args, "vocab_path", None) and os.path.exists(args.vocab_path):
        tokenizer.load_vocab(args.vocab_path)
        console.print("[green]Vocab cargado[/green]")
    else:
        raise ValueError("Necesitas vocab.json para entrenar")

    # -------- Dataset --------
    dataset = get_dataset(args, tokenizer)

    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size

    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0  # 🔥 mejor para CPU débil
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size
    )

    # -------- Modelo --------
    model_config = {
        "vocab_size": tokenizer.vocab_size,
        "block_size": args.block_size
    }

    model = get_model(args.model_name, model_config).to(args.device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate
    )

    # -------- Entrenamiento --------
    best_val = float("inf")
    patience_counter = 0

    os.makedirs("checkpoints", exist_ok=True)

    for epoch in range(args.max_iters):

        train_loss = train_epoch(model, train_loader, optimizer, args.device)
        val_loss = eval_epoch(model, val_loader, args.device)

        console.print(
            f"[bold]Epoch {epoch+1}[/bold] | "
            f"train: {train_loss:.4f} | val: {val_loss:.4f}"
        )

        # Guardar
        torch.save(model.state_dict(), f"checkpoints/model_{epoch+1}.pt")

        # Early stopping
        if val_loss < best_val:
            best_val = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), "checkpoints/best.pt")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                console.print("[red]Early stopping[/red]")
                break

    console.print("[bold green]Entrenamiento finalizado[/bold green]")




