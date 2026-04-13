# =========================================================
# 🔹 MEMORY MANAGER (FAISS VERSION - RAG READY)
# =========================================================
import time
import random
import json
import os
import torch
import torch.nn.functional as F
import numpy as np
import faiss

from .memory_unit import MemoryUnit


class MemoryManager:
    def __init__(self, tokenizer=None, model=None, device="cpu"):
        self.memory = []

        self.tokenizer = tokenizer
        self.model = model
        self.device = device

        # 🔥 dimensión embeddings
        self.embedding_dim = model.hidden_size if model else 256

        # 🔥 FAISS index (cosine similarity vía inner product)
        self.index = faiss.IndexFlatIP(self.embedding_dim)

        # 🔥 mapa índice → memoria
        self.index_to_memory = []

    # =====================================================
    # 🔹 EMBEDDING
    # =====================================================
    def _encode_text(self, text):
        if self.model is None or self.tokenizer is None:
            return None

        tokens = self.tokenizer.encode(text)

        # 🔥 limitar tamaño
        tokens = tokens[:self.model.block_size]

        x = torch.tensor([tokens], dtype=torch.long).to(self.device)

        with torch.no_grad():
            # 🔥 forward parcial del modelo (embedding contextual)
            tok = self.model.token_embedding(x)

            T = x.size(1)
            pos = torch.arange(0, T, device=self.device).unsqueeze(0)
            pos = self.model.pos_embedding(pos)

            h = tok + pos

            for block in self.model.blocks:
                h = block(h)

            h = self.model.ln_f(h)

            # 🔥 pooling
            emb = h.mean(dim=1)

        emb = emb.squeeze(0)

        # 🔥 NORMALIZACIÓN (clave para cosine)
        emb = emb / (emb.norm(p=2) + 1e-8)

        return emb

    # =====================================================
    # 🔹 ADD MEMORY
    # =====================================================
    def add_candidate(self, content, importance=0.5, origin=None):
        mem = MemoryUnit(content, confidence=importance, origin=origin)

        mem.embedding = self._encode_text(content)

        if mem.embedding is not None:
            vec = mem.embedding.detach().cpu().numpy().astype("float32")

            self.index.add(vec.reshape(1, -1))
            self.index_to_memory.append(mem)

        self.memory.append(mem)
        return mem

    # =====================================================
    # 🔹 RETRIEVE (FAISS)
    # =====================================================
    def retrieve(self, query=None, top_k=5):
        if not self.index_to_memory:
            return []

        if query is None:
            return self.memory[:top_k]

        query_emb = self._encode_text(query)

        if query_emb is None:
            return []

        vec = query_emb.detach().cpu().numpy().astype("float32").reshape(1, -1)

        scores, indices = self.index.search(vec, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.index_to_memory):
                m = self.index_to_memory[idx]

                if m.state == "activa":
                    m.last_access = time.time()
                    m.frequency += 1
                    results.append(m)

        return results

    # =====================================================
    # 🔹 EVALUATE
    # =====================================================
    def evaluate(self, memories):
        evaluated = []

        for m in memories:
            if random.random() < m.confidence:
                evaluated.append(m.content)
                m.reinforce(0.05)
            else:
                m.degrade(0.02)

        return evaluated

    # =====================================================
    # 🔹 PROCESS EVENTS
    # =====================================================
    def process_events(self, events):
        if not events:
            return

        for e in events:
            if isinstance(e, MemoryUnit):
                e.embedding = self._encode_text(e.content)
                self.memory.append(e)

                if e.embedding is not None:
                    vec = e.embedding.cpu().numpy().astype("float32")
                    self.index.add(vec.reshape(1, -1))
                    self.index_to_memory.append(e)

            elif isinstance(e, dict) and "content" in e:
                self.add_candidate(
                    e["content"],
                    e.get("importance", 0.5),
                    e.get("origin")
                )

    # =====================================================
    # 🔹 CLEANING
    # =====================================================
    def compress_memory(self):
        unique = {}

        for m in self.memory:
            if m.state != "descartada":
                unique[m.content] = m

        self.memory = list(unique.values())

        # 🔥 reconstruir índice
        self.rebuild_index()

    def decay_memory(self):
        for m in self.memory:
            m.degrade(0.01)

    # =====================================================
    # 🔹 REBUILD INDEX (IMPORTANTE)
    # =====================================================
    def rebuild_index(self):
        self.index.reset()
        self.index_to_memory = []

        for m in self.memory:
            if m.embedding is not None and m.state == "activa":
                vec = m.embedding.cpu().numpy().astype("float32")
                self.index.add(vec.reshape(1, -1))
                self.index_to_memory.append(m)

    # =====================================================
    # 🔹 SAVE / LOAD
    # =====================================================
    def save(self, path="checkpoints/memory.json"):
        data = []

        for m in self.memory:
            data.append({
                "content": m.content,
                "confidence": m.confidence,
                "origin": m.origin,
                "frequency": m.frequency,
                "last_access": m.last_access,
                "state": m.state,
                "embedding": m.embedding.tolist() if m.embedding is not None else None
            })

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 🔥 guardar índice FAISS
        self.save_index()

    def load(self, path="checkpoints/memory.json"):
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.memory = []
        self.index_to_memory = []
        self.index.reset()

        for d in data:
            mem = MemoryUnit(d["content"], d["confidence"], d["origin"])

            mem.frequency = d["frequency"]
            mem.last_access = d["last_access"]
            mem.state = d["state"]

            if d.get("embedding") is not None:
                emb = torch.tensor(d["embedding"], dtype=torch.float32)
                emb = emb / (emb.norm(p=2) + 1e-8)
                mem.embedding = emb

                vec = emb.cpu().numpy().astype("float32")
                self.index.add(vec.reshape(1, -1))
                self.index_to_memory.append(mem)

            self.memory.append(mem)

    # =====================================================
    # 🔹 FAISS SAVE / LOAD
    # =====================================================
    def save_index(self, path="checkpoints/faiss.index"):
        faiss.write_index(self.index, path)

    def load_index(self, path="checkpoints/faiss.index"):
        if os.path.exists(path):
            self.index = faiss.read_index(path)