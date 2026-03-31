# utils/tokenizer.py
import re
import json
from typing import List, Iterable
from utils.silabificador import Silabificador


class SyllableTokenizer:

    CLEAN_REGEX = re.compile(r"[^a-záéíóúüñ¿?¡!.,;:—\"' \n]")

    def __init__(self, vocab=None):

        self.replacements = {
            "á": "a", "é": "e", "í": "i",
            "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
        }

        self.special_tokens = [
            "<PAD>", "<UNK>", "<BOS>", "<EOS>", "<SEP>",
            "<CLS>", "<MASK>", "<PROMPT>", "<RESPONSE>",
            "<THINK>", "<ANSWER>", "<SYS>", "<USR>", "<BOT>",
            "<COMA>", "<PUNTO>",
            "<INTERROGACION_ABRE>", "<INTERROGACION_CIERRA>",
            "<ADMIRACION_ABRE>", "<ADMIRACION_CIERRA>",
            "<PUNTO_Y_COMA>", "<DOS_PUNTOS>",
            "<GUION>", "<GUION_LARGO>",
            "<COMILLAS_ABRE>", "<COMILLAS_CIERRA>",
            "<COMILLAS_SIMPLES_ABRE>", "<COMILLAS_SIMPLES_CIERRA>",
            "<SPACE>", "<NEWLINE>", "<TAB>"
        ]

        self.vocab = list(self.special_tokens) + (vocab or [])
        self._rebuild_mappings()

        # 🔥 CACHE
        self.word_cache = {}
        self.syllable_cache = {}

    # ------------------------
    # MAPPINGS
    # ------------------------
    def _rebuild_mappings(self):
        self.stoi = {tok: i for i, tok in enumerate(self.vocab)}
        self.itos = {i: tok for i, tok in enumerate(self.vocab)}

        self.pad_token_id = self.stoi.get("<PAD>", 0)
        self.unk_token_id = self.stoi.get("<UNK>", 1)
        self.bos_token_id = self.stoi.get("<BOS>", 2)
        self.eos_token_id = self.stoi.get("<EOS>", 3)

        self.vocab_size = len(self.vocab)

    # ------------------------
    # CLEAN
    # ------------------------
    def clean_text(self, text: str) -> str:
        if text is None:
            return ""
        text = str(text).lower()
        return self.CLEAN_REGEX.sub(" ", text)

    def apply_replacements(self, text: str) -> str:
        for k, v in self.replacements.items():
            text = text.replace(k, v)
        return text

    def text_to_token_markers(self, text: str) -> str:
        return (
            text.replace(",", " <COMA> ")
                .replace(".", " <PUNTO> ")
                .replace(";", " <PUNTO_Y_COMA> ")
                .replace(":", " <DOS_PUNTOS> ")
                .replace("-", " <GUION> ")
                .replace("—", " <GUION_LARGO> ")
                .replace("\"", " <COMILLAS_ABRE> ")
                .replace("'", " <COMILLAS_SIMPLES_ABRE> ")
                .replace("?", " <INTERROGACION_CIERRA> ")
                .replace("¿", " <INTERROGACION_ABRE> ")
                .replace("!", " <ADMIRACION_CIERRA> ")
                .replace("¡", " <ADMIRACION_ABRE> ")
                .replace(" ", " <SPACE> ")
                .replace("\n", " <NEWLINE> ")
        )

    # ------------------------
    # ENCODE (OPTIMIZADO)
    # ------------------------
    def encode(self, text: str, add_bos=True, add_eos=True) -> List[int]:
        tokens = []

        if add_bos:
            tokens.append(self.bos_token_id)

        text = self.clean_text(text)
        text = self.text_to_token_markers(text)
        text = self.apply_replacements(text)

        for word in text.split():

            # 🔥 CACHE palabra
            if word in self.word_cache:
                tokens.extend(self.word_cache[word])
                continue

            if word in self.stoi:
                encoded = [self.stoi[word]]
            else:
                # 🔥 CACHE sílabas
                if word not in self.syllable_cache:
                    try:
                        sylls = Silabificador.split_into_syllables(word)
                    except Exception:
                        sylls = [word]

                    self.syllable_cache[word] = sylls

                encoded = [
                    self.stoi.get(s, self.unk_token_id)
                    for s in self.syllable_cache[word]
                ]

            self.word_cache[word] = encoded
            tokens.extend(encoded)

        if add_eos:
            tokens.append(self.eos_token_id)

        return tokens

    # ------------------------
    # DECODE
    # ------------------------
    def decode(self, token_ids: Iterable[int]) -> str:
        out = []

        for tid in token_ids:
            tok = self.itos.get(int(tid), "<UNK>")

            if tok == "<COMA>":
                out.append(",")
            elif tok == "<PUNTO>":
                out.append(".")
            elif tok == "<SPACE>":
                out.append(" ")
            elif tok == "<NEWLINE>":
                out.append("\n")
            else:
                if not tok.startswith("<"):
                    out.append(tok)

        return "".join(out)

    # ------------------------
    # VOCAB
    # ------------------------
    def build_vocab(self, texts: Iterable[str]):
        unique = set()

        for text in texts:
            text = self.clean_text(text)
            text = self.text_to_token_markers(text)
            text = self.apply_replacements(text)

            for word in text.split():
                if word.startswith("<") and word.endswith(">"):
                    unique.add(word)
                else:
                    if word not in self.syllable_cache:
                        try:
                            sylls = Silabificador.split_into_syllables(word)
                        except Exception:
                            sylls = [word]
                        self.syllable_cache[word] = sylls

                    for s in self.syllable_cache[word]:
                        unique.add(s)

        sorted_vocab = sorted(unique)

        self.vocab = list(self.special_tokens) + sorted_vocab
        self._rebuild_mappings()

        # 🔥 limpiar caches
        self.word_cache.clear()
        self.syllable_cache.clear()

    # ------------------------
    # SAVE / LOAD
    # ------------------------
    def save_vocab(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"vocab": self.vocab}, f, ensure_ascii=False, indent=2)

    def load_vocab(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.vocab = data["vocab"] if isinstance(data, dict) else data
        self._rebuild_mappings()

        # 🔥 limpiar caches
        self.word_cache.clear()
        self.syllable_cache.clear()




