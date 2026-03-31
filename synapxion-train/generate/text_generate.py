# text_generate.py
import argparse
import torch
import torch.nn.functional as F
import json
import os

from utils.tokenizer import SyllableTokenizer

# -------------------------
# 🔹 MODEL FACTORY (igual que en train)
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
# 🔹 SAMPLING
# -------------------------
def top_k_top_p_filter_logits(logits, top_k=0, top_p=0.0):
    logits = logits.clone()

    # Top-k
    if top_k > 0:
        values, indices = torch.topk(logits, top_k)
        mask = torch.ones_like(logits, dtype=torch.bool)
        mask[indices] = False
        logits[mask] = -1e10

    # Top-p
    if top_p > 0.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        probs = F.softmax(sorted_logits, dim=-1)
        cumulative_probs = torch.cumsum(probs, dim=-1)

        cutoff = cumulative_probs > top_p
        cutoff[0] = False

        remove_indices = sorted_indices[cutoff]
        logits[remove_indices] = -1e10

    return logits


def sample_next_token(logits, temperature=1.0, top_k=0, top_p=0.0):
    logits = logits / max(temperature, 1e-5)

    if torch.isnan(logits).any():
        logits = torch.nan_to_num(logits)

    logits = top_k_top_p_filter_logits(logits, top_k, top_p)

    probs = F.softmax(logits, dim=-1)
    return torch.multinomial(probs, num_samples=1).item()

# -------------------------
# 🔹 GENERATION
# -------------------------
def generate_text(model, tokenizer, prompt, args, device):
    model.eval()

    tokens = tokenizer.encode(prompt, add_bos=True, add_eos=False)
    input_ids = torch.tensor(tokens, dtype=torch.long, device=device).unsqueeze(0)

    for _ in range(args.max_new_tokens):
        idx_cond = input_ids[:, -model.block_size:]

        with torch.no_grad():
            logits = model(idx_cond)

        logits = logits[0, -1, :]

        next_token = sample_next_token(
            logits,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p
        )

        next_token_tensor = torch.tensor([[next_token]], device=device)
        input_ids = torch.cat([input_ids, next_token_tensor], dim=1)

    return tokenizer.decode(input_ids[0].tolist())

# -------------------------
# 🔹 LOADERS
# -------------------------
def load_tokenizer(path):
    tok = SyllableTokenizer()

    if not os.path.exists(path):
        raise ValueError("vocab.json no encontrado")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tok.vocab = data["vocab"] if isinstance(data, dict) else data
    tok._rebuild_mappings()

    return tok


def load_model(args, tokenizer, device):
    config = {
        "vocab_size": tokenizer.vocab_size,
        "block_size": args.block_size
    }

    model = get_model(args.model, config)

    if not os.path.exists(args.checkpoint):
        raise ValueError("Checkpoint no encontrado")

    state = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(state)

    model.to(device)
    model.eval()

    return model

# -------------------------
# 🔹 MAIN
# -------------------------
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--checkpoint", type=str, default="checkpoints/best.pt")
    parser.add_argument("--vocab", type=str, default="checkpoints/vocab.json")
    parser.add_argument("--model", type=str, default="base")

    parser.add_argument("--prompt", type=str, default="Hola, ¿cómo estás?")
    parser.add_argument("--max-new-tokens", type=int, default=100)

    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--top-p", type=float, default=0.9)

    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--block-size", type=int, default=128)

    args = parser.parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available() and args.device == "cuda" else "cpu"
    )

    print(f"Usando device: {device}")

    tokenizer = load_tokenizer(args.vocab)
    model = load_model(args, tokenizer, device)

    output = generate_text(model, tokenizer, args.prompt, args, device)

    print("\n=== Generación ===\n")
    print(output)
    print("\n==================\n")


if __name__ == "__main__":
    main()




