# gptMini.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from .baseModel import baseModel

class GPTMini(baseModel):
    def __init__(
        self,
        vocab_size,
        block_size,
        d_model=96,          # 🔥 más pequeño para CPU
        nhead=4,             # 🔥 menos heads
        num_layers=4,        # 🔥 menos capas
        dropout=0.1
    ):
        super().__init__()

        self.block_size = block_size

        # Embeddings
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Embedding(block_size, d_model)

        # 🔥 posiciones precomputadas
        self.register_buffer(
            "pos_ids",
            torch.arange(block_size).unsqueeze(0),
            persistent=False
        )

        # Transformer optimizado (ligero)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu"  # 🔥 mejor que relu
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        self.ln = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size)

        self.dropout = nn.Dropout(dropout)

        # 🔥 inicialización mejorada
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx):
        B, T = idx.size()

        # 🔥 seguridad
        assert T <= self.block_size, "Sequence too long"

        pos = self.pos_ids[:, :T]

        x = self.embed(idx) + self.pos_embed(pos)
        x = self.dropout(x)

        x = self.transformer(x)
        x = self.ln(x)

        logits = self.head(x)

        return logits

    def generate(self, idx, max_new_tokens=50):
        """Generación simple (para pruebas)"""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits = self(idx_cond)

            logits = logits[:, -1, :]
            probs = F.softmax(logits, dim=-1)

            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)

        return idx




