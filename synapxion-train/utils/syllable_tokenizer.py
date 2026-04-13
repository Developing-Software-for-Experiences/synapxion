import json
import unicodedata
from typing import List, Iterable
from .silabificador import SilabificadorFast


class SyllableTokenizer:
    def __init__(self, vocab: List[str] = None):
        self.special_tokens = [
            "<PAD>", "<UNK>", "<BOS>", "<EOS>", "<NUM>",

            "<SPACE>", "<NEWLINE>", "<TAB>",

            "<PROMPT>", "<THINK>", "<ANSWER>", "<OUTPUT>", "<MEMORY>", "</MEMORY>"

            "<COMA>", "<PUNTO>",
            "<INTERROGACION_ABRE>", "<INTERROGACION_CIERRA>",
            "<ADMIRACION_ABRE>", "<ADMIRACION_CIERRA>",
            "<DOS_PUNTOS>", "<PUNTO_Y_COMA>",

            "<GUION>", "<GUION_LARGO>",

            "<COMILLA_SIMPLE>", "<COMILLA_DOBLE>",
            "<PARENTESIS_ABRE>", "<PARENTESIS_CIERRA>",
            "<CORCHETE_ABRE>", "<CORCHETE_CIERRA>",
            "<LLAVE_ABRE>", "<LLAVE_CIERRA>",

            "<SLASH>", "<BACKSLASH>",
            "<IGUAL>", "<MENOR>", "<MAYOR>", "<PIPE>",

            "<PORCENTAJE>", "<DOLAR>", "<AMPERSAND>",
            "<CIRCUNFLEJO>", "<TILDE>", "<BACKTICK>",
            "<GRADO>", "<NEGACION>", "<ASTERISCO>",
            "<ACENTO_AGUDO>",

            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
        ]

        self.vocab = list(self.special_tokens) + (vocab or [])
        self._rebuild_mappings()

        self.word_cache = {}
        self.syllable_cache = {}

        self.allow_whole_word_tokens = True

    # =========================
    # MAPPINGS
    # =========================
    def _rebuild_mappings(self):
        self.stoi = {tok: i for i, tok in enumerate(self.vocab)}
        self.itos = {i: tok for i, tok in enumerate(self.vocab)}

        self.pad_token_id = self.stoi["<PAD>"]
        self.unk_token_id = self.stoi["<UNK>"]
        self.bos_token_id = self.stoi["<BOS>"]
        self.eos_token_id = self.stoi["<EOS>"]

    # =========================
    # HELPERS
    # =========================
    def is_valid_char(self, c: str) -> bool:
        return (
            c.isalpha()
            or c.isdigit()
            or c.isspace()
            or self.get_punctuation_token(c) is not None
            or ord(c) < 256  # 🔥 soporte unicode básico
        )

    def is_word_char(self, c: str) -> bool:
        return c.isalpha() or c == "_"

    def get_punctuation_token(self, c: str):
        return {
            ',': "<COMA>", '.': "<PUNTO>",
            '?': "<INTERROGACION_CIERRA>", '¿': "<INTERROGACION_ABRE>",
            '!': "<ADMIRACION_CIERRA>", '¡': "<ADMIRACION_ABRE>",
            ':': "<DOS_PUNTOS>", ';': "<PUNTO_Y_COMA>",
            '-': "<GUION>", '—': "<GUION_LARGO>",
            "'": "<COMILLA_SIMPLE>", '"': "<COMILLA_DOBLE>",
            '(': "<PARENTESIS_ABRE>", ')': "<PARENTESIS_CIERRA>",
            '[': "<CORCHETE_ABRE>", ']': "<CORCHETE_CIERRA>",
            '{': "<LLAVE_ABRE>", '}': "<LLAVE_CIERRA>",
            '/': "<SLASH>", '\\': "<BACKSLASH>",
            '=': "<IGUAL>", '<': "<MENOR>", '>': "<MAYOR>",
            '|': "<PIPE>", '%': "<PORCENTAJE>",
            '$': "<DOLAR>", '&': "<AMPERSAND>",
            '^': "<CIRCUNFLEJO>", '~': "<TILDE>",
            '`': "<BACKTICK>", '°': "<GRADO>",
            '¬': "<NEGACION>", '*': "<ASTERISCO>",
            '´': "<ACENTO_AGUDO>"
        }.get(c)

    # =========================
    # SILABAS
    # =========================
    def split_into_syllables(self, word: str):
        if word in self.syllable_cache:
            return self.syllable_cache[word]

        syllables = SilabificadorFast.split_into_syllables(word)
        self.syllable_cache[word] = syllables
        return syllables

    # =========================
    # ENCODE
    # =========================
    def encode(self, text: str, add_bos=True, add_eos=True):
        tokens = []
        self.encode_to_stream(text, tokens.append, add_bos, add_eos)
        return tokens

    # =========================
    # STREAMING
    # =========================
    def encode_to_stream(self, text: str, emit, add_bos=True, add_eos=True):
        # 🔥 Normalización unicode (CLAVE)
        text = unicodedata.normalize("NFKC", text)

        if add_bos:
            emit(self.bos_token_id)

        buffer = []
        i = 0

        def flush_word():
            if not buffer:
                return

            word = "".join(buffer)
            buffer.clear()

            if self.allow_whole_word_tokens and word in self.stoi:
                emit(self.stoi[word])
                return

            if word in self.word_cache:
                for t in self.word_cache[word]:
                    emit(t)
            else:
                syllables = self.split_into_syllables(word)
                ids = [self.stoi.get(s, self.unk_token_id) for s in syllables]

                for t in ids:
                    emit(t)

                self.word_cache[word] = ids

        while i < len(text):
            c = text[i]

            # 🔹 tokens especiales tipo <PROMPT>
            if c == "<":
                flush_word()
                j = i + 1
                while j < len(text) and text[j] != ">":
                    j += 1

                if j < len(text):
                    candidate = text[i:j+1]
                    if candidate in self.stoi:
                        emit(self.stoi[candidate])
                        i = j + 1
                        continue

            # 🔹 caracteres inválidos
            if not self.is_valid_char(c):
                flush_word()
                emit(self.unk_token_id)
                i += 1
                continue

            # 🔹 palabra
            if self.is_word_char(c) and not c.isdigit():
                buffer.append(c)
                i += 1
                continue

            flush_word()

            # 🔹 dígitos
            if c.isdigit():
                emit(self.stoi.get(c, self.unk_token_id))

            # 🔹 espacios
            elif c.isspace():
                if c == '\n':
                    emit(self.stoi["<NEWLINE>"])
                elif c == '\t':
                    emit(self.stoi["<TAB>"])
                else:
                    emit(self.stoi["<SPACE>"])

            # 🔹 puntuación
            else:
                punc = self.get_punctuation_token(c)
                emit(self.stoi.get(punc, self.unk_token_id) if punc else self.unk_token_id)

            i += 1

        flush_word()

        if add_eos:
            emit(self.eos_token_id)

    # =========================
    # DECODE
    # =========================
    def decode(self, token_ids: Iterable[int]) -> str:
        out = []

        for tid in token_ids:
            tok = self.itos.get(tid, "<UNK>")

            if tok == "<SPACE>":
                out.append(" ")
            elif tok == "<NEWLINE>":
                out.append("\n")
            elif tok == "<TAB>":
                out.append("\t")
            elif not tok.startswith("<"):
                out.append(tok)

        return "".join(out)

    # =========================
    # TOKEN ID
    # =========================
    def token_to_id(self, token: str) -> int:
        return self.stoi.get(token, self.unk_token_id)

    # =========================
    # SAVE / LOAD
    # =========================
    def load_vocab(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "vocab" in data:
            self.vocab = data["vocab"]
        elif "indexed" in data:
            indexed = data["indexed"]
            self.vocab = [indexed[str(i)] for i in range(len(indexed))]
        else:
            raise ValueError("Formato desconocido")

        self._rebuild_mappings()
        self.word_cache.clear()
        self.syllable_cache.clear()