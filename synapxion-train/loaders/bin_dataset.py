import torch
import random
import numpy as np
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset

# =========================================================
# 🔹 PRESETS (🔥 CLAVE)
# =========================================================
PRESETS = {
    "completion": {
        "train_on": ["ALL"]
    },
    "chat": {
        "train_on": ["ANSWER"]
    },
    "reasoning": {
        "train_on": ["THINK", "ANSWER"]
    },
    "instruction": {
        "train_on": ["ANSWER"]
    },
    "multimodal": {
        "train_on": ["OUTPUT"]
    }
}

# =========================================================
# 🔹 BIN SOURCE
# =========================================================
class BinSource:
    def __init__(self, bin_path, idx_path):
        self.tokens = np.memmap(bin_path, dtype=np.int32, mode="r")
        self.entries = self._load_idx(idx_path)

    def _load_idx(self, path):
        with open(path, "rb") as f:
            if f.read(8) != b"SYNIDXv2":
                raise ValueError("IDX inválido")

            count = int.from_bytes(f.read(8), "little")
            entries = np.fromfile(f, dtype=np.int64, count=count * 3)

            return entries.reshape(-1, 3)

    def __len__(self):
        return len(self.entries)

    def get(self, idx):
        offset, length, targetStart = self.entries[idx]

        tokens = np.array(
            self.tokens[offset: offset + length],
            dtype=np.int32
        )

        return tokens, int(targetStart)


# =========================================================
# 🔹 HF SOURCE
# =========================================================
class HFSource:
    def __init__(self, dataset):
        self.ds = dataset

    def __len__(self):
        return len(self.ds)

    def get(self, idx):
        return self.ds[idx]


# =========================================================
# 🔹 FORMATTER
# =========================================================
class Formatter:
    def format(self, item):
        keys = item.keys()

        if "text" in keys:
            return item["text"]

        if "instruction" in keys and "output" in keys:
            return f"<PROMPT> {item['instruction']} <ANSWER> {item['output']}"

        if "prompt" in keys and "response" in keys:
            return f"<PROMPT> {item['prompt']} <ANSWER> {item['response']}"

        if "input" in keys and "output" in keys:
            return f"<PROMPT> {item['input']} <OUTPUT> {item['output']}"

        if "conversations" in keys:
            parts = []
            for msg in item["conversations"]:
                role = msg.get("from") or msg.get("role")
                text = msg.get("value") or msg.get("content")

                if role in ["user", "human"]:
                    parts.append(f"<PROMPT> {text}")
                elif role in ["assistant", "gpt"]:
                    parts.append(f"<ANSWER> {text}")

            return " ".join(parts)

        print("⚠️ Unknown format:", item)
        return None


# =========================================================
# 🔹 PROCESSOR
# =========================================================
class Processor:
    def __init__(self, tokenizer, block_size, preset):
        self.tokenizer = tokenizer
        self.block_size = block_size
        self.preset = PRESETS[preset]

        self.special = {
            "PROMPT": tokenizer.token_to_id_fn("<PROMPT>"),
            "THINK": tokenizer.token_to_id_fn("<THINK>"),
            "ANSWER": tokenizer.token_to_id_fn("<ANSWER>"),
            "OUTPUT": tokenizer.token_to_id_fn("<OUTPUT>"),
        }

        self.formatter = Formatter()

    # -------------------------
    def mask_tokens(self, tokens, y):
        if "ALL" in self.preset["train_on"]:
            return y

        mask = torch.ones_like(y) * -100
        current = None

        for i, t in enumerate(tokens[:-1]):
            for role, tid in self.special.items():
                if t == tid:
                    current = role

            if current in self.preset["train_on"]:
                mask[i] = y[i]

        mask[y == self.tokenizer.pad_id] = -100
        return mask

    # -------------------------
    def process_bin(self, tokens, targetStart):
        tokens = tokens[:self.block_size]

        if len(tokens) < self.block_size:
            tokens = list(tokens) + [self.tokenizer.pad_id] * (self.block_size - len(tokens))

        x = torch.tensor(tokens[:-1]).long()
        y = torch.tensor(tokens[1:]).long()

        y[:max(0, targetStart - 1)] = -100
        return x, y

    # -------------------------
    def process_raw(self, item):
        text = self.formatter.format(item)
        if text is None:
            return None

        text += " <EOS>"

        tokens = self.tokenizer.encode(text)[:self.block_size]

        if len(tokens) < self.block_size:
            tokens += [self.tokenizer.pad_id] * (self.block_size - len(tokens))

        x = torch.tensor(tokens[:-1]).long()
        y = torch.tensor(tokens[1:]).long()

        y = self.mask_tokens(tokens, y)
        return x, y

    # -------------------------
    def process(self, sample):
        if isinstance(sample, tuple):  # BIN
            return self.process_bin(*sample)
        return self.process_raw(sample)


# =========================================================
# 🔹 DATASET
# =========================================================
class UnifiedDataset(Dataset):
    def __init__(self, sources, processor):
        self.sources = sources
        self.processor = processor

        self.mapping = []
        for i, src in enumerate(sources):
            for j in range(len(src)):
                self.mapping.append((i, j))

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, idx):
        for _ in range(10):
            src_id, local_idx = self.mapping[idx]
            src = self.sources[src_id]

            sample = src.get(local_idx)
            processed = self.processor.process(sample)

            if processed is not None:
                return processed

            idx = (idx + 1) % len(self.mapping)

        raise RuntimeError("Too many invalid samples")


# =========================================================
# 🔹 BUILDER
# =========================================================
def build_dataloaders(args, tokenizer, device):
    from torch.utils.data import random_split

    sources = []

    # BIN
    for d in getattr(args, "bin_datasets", []):
        sources.append(BinSource(d["bin"], d["idx"]))

    # HF
    for d in getattr(args, "hf_datasets", []):
        ds = load_dataset(
            d["name"],
            d.get("config"),
            split=d.get("split", "train")
        )
        sources.append(HFSource(ds))

    if not sources:
        raise ValueError("No datasets")

    processor = Processor(
        tokenizer,
        args.block_size,
        preset=getattr(args, "preset", "chat")
    )

    dataset = UnifiedDataset(sources, processor)

    train_size = int(0.9 * len(dataset))
    val_size = max(1, len(dataset) - train_size)

    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    pin = device.type == "cuda"

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        pin_memory=pin
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        pin_memory=pin
    )

    return train_loader, val_loader, None, {}