import torch
import torch.nn as nn
import torch.nn.functional as F

class baseModel(nn.Module):
    def forward(self, x):
        raise NotImplementedError

    def generate(self, x, max_new_tokens=50):
        raise NotImplementedError




