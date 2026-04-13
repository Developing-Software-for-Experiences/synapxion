import os
import glob
import torch
import argparse
import shutil
import gc
from train import run_training
from models import AssistantModel
from monrix import MemoryManager

from rich.console import Console
console = Console()

# 🔹 LIMITACIÓN DE RECURSOS (Antes de cualquier otro import de torch/numpy)
def limit_resources(threads=4):
    os.environ["OMP_NUM_THREADS"] = str(threads)
    os.environ["MKL_NUM_THREADS"] = str(threads)
    torch.set_num_threads(threads)
    print(f"[ResourceControl] Limitado a {threads} núcleos de CPU.")

class Args:
    pass

# =========================================================
# 🔹 BUILD ARGS
# =========================================================
def build_args(cli_args, online_datasets):
    args = Args()
    args.mode = cli_args.mode
    args.input_dir = cli_args.input_dir
    args.output_dir = cli_args.output_dir
    args.preset = "reasoning"
    
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)

    # Carga de datasets locales
    bin_files = glob.glob(os.path.join(args.input_dir, "*.bin"))
    idx_files = glob.glob(os.path.join(args.input_dir, "*.idx"))
    args.bin_datasets = []

    for b in bin_files:
        name = os.path.splitext(os.path.basename(b))[0]
        idx_match = [i for i in idx_files if name in i]
        if idx_match:
            args.bin_datasets.append({"bin": b, "idx": idx_match[0]})
    
    # Datasets online
    args.hf_datasets = [{"name": d["name"], "config": d.get("config"), "split": d.get("split", "train")} 
                       for d in online_datasets]

    args.vocab_path = os.path.join(args.input_dir, "vocab.json")
    args.model_name = cli_args.model_name
    args.block_size = cli_args.block_size
    args.batch_size = cli_args.batch_size
    args.learning_rate = cli_args.learning_rate
    args.max_iters = cli_args.max_iters
    
    return args

# =========================================================
# 🔹 INFERENCE (OPTIMIZADA PARA RAM)
# =========================================================
def run_inference(prompt="Hola", args=None):
    vocab_path = os.path.join("checkpoints", "vocab.json")
    checkpoint_path = os.path.join("checkpoints", "best.pt")

    if not os.path.exists(vocab_path) or not os.path.exists(checkpoint_path):
        console.print("[red]Error: Faltan archivos en 'checkpoints/'[/red]")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    from train import load_tokenizer
    class DummyArgs:
        vocab_path = vocab_path
        merges_path = vocab_path

    tokenizer = load_tokenizer(DummyArgs)
    
    # 1. Cargar modelo base
    model = AssistantModel(
        vocab_size=len(tokenizer.token_to_id),
        block_size=args.block_size
    ).to(device)

    # 2. Cargar pesos y liberar memoria temporal
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    
    # 3. 🔥 MODO TURBO (Cuantización para ahorrar RAM)
    if device.type == "cpu":
        model = model.to_turbo()
    
    model.eval()

    # 🧠 MEMORIA
    memory_manager = MemoryManager()
    memory_manager.load()
    mems = memory_manager.retrieve(prompt)
    selected_mems = memory_manager.evaluate(mems)

    # Generación
    output = model.generate(
        prompt,
        tokenizer,
        memory_context=selected_mems,
        device=device.type,
    )

    clean = output.split("Assistant:")[-1].strip()
    console.print(f"\n[bold green]Synapxion:[/bold green] {clean}\n")

    # Guardar en memoria y limpiar RAM
    memory_manager.add_candidate(f"U: {prompt} A: {clean}", importance=0.6)
    memory_manager.save()
    
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

# =========================================================
# 🔹 MAIN
# =========================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "inference"], default="train")
    parser.add_argument("--threads", type=int, default=4, help="Límite de núcleos CPU")
    parser.add_argument("--input_dir", type=str, default="input")
    parser.add_argument("--output_dir", type=str, default="output")
    parser.add_argument("--model_name", type=str, default="assistant")
    parser.add_argument("--block_size", type=int, default=256)
    parser.add_argument("--batch_size", type=int, default=16) # Bajado para ahorrar RAM
    parser.add_argument("--learning_rate", type=float, default=3e-4)
    parser.add_argument("--max_iters", type=int, default=10)

    cli_args = parser.parse_args()
    limit_resources(cli_args.threads)

    online_datasets = []
    if cli_args.mode == "train":
        use_online = input("¿Cargar datasets en línea? (s/n): ").strip().lower()
        if use_online == "s":
            while True:
                name = input("Dataset (HuggingFace): ").strip()
                online_datasets.append({"name": name, "config": None, "split": "train"})
                if input("¿Otro? (s/n): ").lower() != "s": break

    args = build_args(cli_args, online_datasets)

    if args.mode == "inference":
        while True:
            p = input("Prompt (o 'exit'): ").strip()
            if p.lower() in ["exit", "salir"]: break
            run_inference(p, args)
    else:
        run_training(args)
        if os.path.exists(args.vocab_path):
            shutil.copy(args.vocab_path, "checkpoints/vocab.json")
        console.print("[yellow]Entrenamiento completado. Entrando en modo prueba...[/yellow]")
        run_inference("Hola, ¿qué puedes hacer?", args)

if __name__ == "__main__":
    main()