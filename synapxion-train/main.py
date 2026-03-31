# main.py
import os
import glob
from training.train import run_training
from generate.text_generate import load_tokenizer, load_model, generate_text
import torch

class Args:
    pass

def build_args():
    args = Args()

    # -------- Paths --------
    args.input_dir = "input"
    args.output_dir = "output"

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)

    # -------- Dataset --------
    # Detectar automáticamente archivos en input/
    bin_files = glob.glob(os.path.join(args.input_dir, "*.bin"))
    idx_files = glob.glob(os.path.join(args.input_dir, "*.idx"))
    txt_files = glob.glob(os.path.join(args.input_dir, "*.txt"))

    if bin_files and idx_files:
        args.use_bin = True
        args.bin_path = bin_files[0]
        args.idx_path = idx_files[0]
        print(f"[INFO] Usando dataset BIN: {args.bin_path}")
    elif txt_files:
        args.use_bin = False
        with open(txt_files[0], "r", encoding="utf-8") as f:
            args.text = f.read()
        print(f"[INFO] Usando dataset TXT: {txt_files[0]}")
    else:
        raise ValueError("No se encontró dataset en /input")

    # -------- Config --------
    args.vocab_path = os.path.join(args.input_dir, "vocab.json")
    args.model_name = "base"

    args.block_size = 128
    args.batch_size = 16
    args.learning_rate = 3e-4
    args.max_iters = 15   # 🔥 prueba rápida
    args.patience = 2

    return args

def run_inference(output_dir, prompt="Hola, ¿cómo estás?"):
    print("\n[INFO] Ejecutando prueba de generación...\n")

    vocab_path = os.path.join("checkpoints", "vocab.json")
    checkpoint_path = os.path.join("checkpoints", "best.pt")

    if not os.path.exists(vocab_path):
        raise ValueError("No se encontró vocab.json")

    if not os.path.exists(checkpoint_path):
        raise ValueError("No se encontró modelo entrenado")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = load_tokenizer(vocab_path)

    class DummyArgs:
        model = "base"
        checkpoint = checkpoint_path
        block_size = 128

    model = load_model(DummyArgs, tokenizer, device)

    output = generate_text(
        model,
        tokenizer,
        prompt,
        args=type("GenArgs", (), {
            "max_new_tokens": 50,
            "temperature": 0.8,
            "top_k": 40,
            "top_p": 0.9
        })(),
        device=device
    )

    print("=== OUTPUT ===\n")
    print(output)
    print("\n==============")

def main():
    args = build_args()

    # -------- Entrenamiento --------
    run_training(args)

    # -------- Prueba --------
    run_inference(args.output_dir)

if __name__ == "__main__":
    main()
