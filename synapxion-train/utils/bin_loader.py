# bin_loader.py
import numpy as np
import torch
from torch.utils.data import Dataset

class BinDataset(Dataset):
    def __init__(self, bin_path, idx_path, max_length=512):
        self.tokens = np.memmap(bin_path, dtype=np.int32, mode="r")
        self.offsets = np.fromfile(idx_path, dtype=np.int64)
        self.max_length = max_length

    def __len__(self):
        return len(self.offsets)

    def __getitem__(self, idx):
        start = self.offsets[idx]
        end = self.offsets[idx + 1] if idx + 1 < len(self.offsets) else len(self.tokens)

        sample = self.tokens[start:end]

        # Truncar
        sample = sample[:self.max_length]

        # Padding
        if len(sample) < self.max_length:
            pad = np.zeros(self.max_length - len(sample), dtype=np.int32)
            sample = np.concatenate([sample, pad])

        return torch.tensor(sample, dtype=torch.long)




