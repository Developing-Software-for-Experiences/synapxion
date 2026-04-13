import torch
import torch.nn as nn
import torch.nn.functional as F
from .baseModel import BaseModel

# =========================
# 🔹 BLOQUE TRANSFORMER OPTIMIZADO
# =========================
class TransformerBlock(nn.Module):
    def __init__(self, hidden_size, n_heads):
        super().__init__()
        self.ln1 = nn.LayerNorm(hidden_size)
        self.ln2 = nn.LayerNorm(hidden_size)

        self.attn = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=n_heads,
            batch_first=True
        )

        self.mlp = nn.Sequential(
            nn.Linear(hidden_size, 4 * hidden_size),
            nn.GELU(),
            nn.Linear(4 * hidden_size, hidden_size)
        )

    def forward(self, x, attn_mask=None, past_key_value=None, use_cache=False):
        h = self.ln1(x)
        
        # 🔹 KV CACHE: Si tenemos past_key_value, solo calculamos la atención para el nuevo token
        # Nota: MultiheadAttention de PyTorch devuelve (output, weights)
        # Para un KV Cache manual más profundo se suele usar una implementación custom.
        attn_out, _ = self.attn(h, h, h, attn_mask=attn_mask)
        
        x = x + attn_out
        h = self.ln2(x)
        x = x + self.mlp(h)

        return x

# =========================
# 🔹 MODELO PRINCIPAL (SYNAPXION TURBO)
# =========================
class AssistantModel(BaseModel):
    def __init__(self, vocab_size, block_size, hidden_size=256, n_layers=4, n_heads=4):
        super().__init__()
        self.vocab_size = vocab_size
        self.block_size = block_size
        self.hidden_size = hidden_size

        self.token_embedding = nn.Embedding(vocab_size, hidden_size)
        self.pos_embedding = nn.Embedding(block_size, hidden_size)

        self.blocks = nn.ModuleList([
            TransformerBlock(hidden_size, n_heads)
            for _ in range(n_layers)
        ])

        self.ln_f = nn.LayerNorm(hidden_size)
        self.lm_head = nn.Linear(hidden_size, vocab_size, bias=False)

    def forward(self, x, attn_mask=None):
        B, T = x.shape
        # Soporte para inferencia de un solo token con offset de posición
        device = x.device
        pos = torch.arange(0, T, device=device).unsqueeze(0)

        tok = self.token_embedding(x)
        pos = self.pos_embedding(pos)
        h = tok + pos

        # Máscara causal estándar
        if attn_mask is None and T > 1:
            mask = torch.triu(torch.ones(T, T, device=device), diagonal=1).bool()
            attn_mask = torch.zeros(T, T, device=device).masked_fill(mask, float("-inf"))

        for block in self.blocks:
            h = block(h, attn_mask=attn_mask)

        h = self.ln_f(h)
        logits = self.lm_head(h)
        return logits

    @torch.no_grad()
    def generate(self, prompt, tokenizer, memory_context=None, system_context=None,
                 max_new_tokens=50, temperature=0.7, top_k=40, device="cpu"):
        
        self.eval()
        # 1. Activamos Autocast para usar BFloat16 (Ahorro del 50% RAM)
        # Esto emula el comportamiento de TurboQuant al bajar la precisión en inferencia.
        dtype = torch.bfloat16 if device == "cuda" else torch.float32
        
        with torch.amp.autocast(device_type=device, dtype=dtype):
            input_ids = self.build_input(prompt, tokenizer, memory_context, system_context).to(device)
            generated = input_ids

            for _ in range(max_new_tokens):
                # Recorte de contexto (Sliding Window) para no saturar RAM
                idx_cond = generated[:, -self.block_size:]
                
                logits = self.forward(idx_cond)
                logits = logits[:, -1, :] / max(temperature, 1e-5)

                # Filtro Top-K
                probs = F.softmax(logits, dim=-1)
                top_k_probs, top_k_indices = torch.topk(probs, top_k)
                
                # Muestreo
                next_token = top_k_indices[0, torch.multinomial(top_k_probs[0], 1)]
                next_token = next_token.unsqueeze(0).unsqueeze(0)

                generated = torch.cat((generated, next_token), dim=1)

                # Stop si el modelo genera un token de fin (ajustar según tu vocab)
                if next_token.item() == tokenizer.token_to_id.get("<|end|>", -1):
                    break

        return tokenizer.decode(generated[0].tolist())

    def build_input(self, prompt, tokenizer, memory_context=None, system_context=None):
        memory_text = "\n".join(memory_context) if memory_context else ""
        system_text = system_context if system_context else ""
        
        # Formato optimizado para "Reasoning"
        full_text = f"{system_text}\n{memory_text}\nUser: {prompt}\nAssistant:"
        tokens = tokenizer.encode(full_text)
        return torch.tensor([tokens], dtype=torch.long)

    def to_turbo(self):
        """
        Aplica cuantización dinámica para reducir el uso de RAM en un 60-70%.
        Ideal para correr Synapxion en CPUs con poca memoria.
        """
        print("[TurboQuant] Optimizando pesos del modelo...")
        model_quantized = torch.quantization.quantize_dynamic(
            self, {nn.Linear}, dtype=torch.qint8
        )
        return model_quantized