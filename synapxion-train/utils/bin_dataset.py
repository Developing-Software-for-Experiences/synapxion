# bin_dataset.py
import numpy as np
import torch
from torch.utils.data import Dataset

class BinDataset(Dataset):
    def __init__(self, bin_path, idx_path, block_size=128):
        self.block_size = block_size
        self.tokens = np.memmap(bin_path, dtype=np.int32, mode="r")
        self.offsets = np.fromfile(idx_path, dtype=np.int64)

    def __len__(self):
        return len(self.offsets)

    def __getitem__(self, idx):
        start = self.offsets[idx]
        end = self.offsets[idx + 1] if idx + 1 < len(self.offsets) else len(self.tokens)

        sample = self.tokens[start:end]

        # 🔥 asegurar longitud mínima
        if len(sample) < 2:
            sample = np.pad(sample, (0, 2 - len(sample)))

        # 🔥 truncar
        sample = sample[:self.block_size]

        # 🔥 padding
        if len(sample) < self.block_size:
            pad = np.zeros(self.block_size - len(sample), dtype=np.int32)
            sample = np.concatenate([sample, pad])

        x = sample[:-1]
        y = sample[1:]

        return (
            torch.from_numpy(x).long(),
            torch.from_numpy(y).long()
        )




