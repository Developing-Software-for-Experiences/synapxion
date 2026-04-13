class HybridTokenizer:
    def __init__(self, syllable_tokenizer, bpe_tokenizer, vocab_dict):
        self.syllable = syllable_tokenizer
        self.bpe = bpe_tokenizer

        self.token_to_id = dict(vocab_dict)
        self.id_to_token = {v: k for k, v in vocab_dict.items()}

        self.pad_id = self.token_to_id.get("<PAD>", 0)
        self.bos_id = self.token_to_id.get("<BOS>", 1)
        self.eos_id = self.token_to_id.get("<EOS>", 2)
        self.unk_id = self.token_to_id.get("<UNK>", 3)

    # =========================
    # 🔹 ENCODE
    # =========================
    def encode(self, text):
        tokens = []
        self.encode_to_stream(text, tokens.append)
        return tokens

    # =========================
    # 🔹 STREAMING
    # =========================
    def encode_to_stream(self, text, emit):
        emit(self.bos_id)

        buffer = []

        def flush():
            if not buffer:
                return

            # 🔥 aplicar BPE sobre tokens (strings)
            merged = self.bpe.apply(buffer)

            for t in merged:
                emit(self.token_to_id.get(t, self.unk_id))

            buffer.clear()

        def handle_token_id(tid):
            tok = self.syllable.itos.get(tid, None)

            if tok is None:
                return

            # 🔥 FLUSH SI ES TOKEN ESPECIAL
            if tok.startswith("<") and tok.endswith(">"):
                flush()
                emit(self.token_to_id.get(tok, self.unk_id))
                return

            buffer.append(tok)

            # 🔥 evitar buffers gigantes
            if len(buffer) >= 32:
                flush()

        # 🔥 usar tokenizer base
        self.syllable.encode_to_stream(
            text,
            handle_token_id,
            add_bos=False,
            add_eos=False
        )

        flush()
        emit(self.eos_id)

    # =========================
    # 🔹 DECODE
    # =========================
    def decode(self, ids):
        out = []

        for i in ids:
            if i in (self.bos_id, self.eos_id, self.pad_id):
                continue

            tok = self.id_to_token.get(i, "<UNK>")

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
    # 🔹 TOKEN ID
    # =========================
    def token_to_id_fn(self, token):
        return self.token_to_id.get(token, self.unk_id)