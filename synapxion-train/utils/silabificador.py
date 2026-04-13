class SilabificadorFast:

    @staticmethod
    def is_vowel(c: str) -> bool:
        return c in "aeiouáéíóúüAEIOUÁÉÍÓÚÜ"

    @staticmethod
    def is_strong(c: str) -> bool:
        return c in "aáeéoóAÁEÉOÓ"

    @staticmethod
    def is_weak(c: str) -> bool:
        return c in "iíuúüIÍUÚÜ"

    @staticmethod
    def has_accent(c: str) -> bool:
        return c in "áéíóúÁÉÍÓÚ"

    @staticmethod
    def is_inseparable(c1: str, c2: str) -> bool:
        pair = (c1.lower(), c2.lower())
        return pair in {
            ('b','r'), ('b','l'),
            ('c','r'), ('c','l'),
            ('d','r'),
            ('f','r'), ('f','l'),
            ('g','r'), ('g','l'),
            ('p','r'), ('p','l'),
            ('t','r')
        }

    # 🔥 CLON DIRECTO DEL ALGORITMO C#
    @staticmethod
    def split_into_syllables(word: str):
        syllables = []

        start = 0
        i = 0
        length = len(word)

        while i < length:
            c = word[i]
            c_lower = c.lower()

            if not SilabificadorFast.is_vowel(c_lower):
                i += 1
                continue

            next_i = i + 1

            # =========================
            # DIPTONGO / HIATO
            # =========================
            if next_i < length:
                v1 = c_lower
                v2 = word[next_i].lower()

                if SilabificadorFast.is_vowel(v2):
                    hiato = (
                        (SilabificadorFast.is_strong(v1) and SilabificadorFast.is_strong(v2)) or
                        (SilabificadorFast.is_strong(v1) and SilabificadorFast.is_weak(v2) and SilabificadorFast.has_accent(v2)) or
                        (SilabificadorFast.is_weak(v1) and SilabificadorFast.is_strong(v2) and SilabificadorFast.has_accent(v1))
                    )

                    if not hiato:
                        i += 1  # 🔥 saltar como en C#

            # =========================
            # CONTAR CONSONANTES
            # =========================
            consonants = 0
            j = i + 1

            while j < length and not SilabificadorFast.is_vowel(word[j].lower()):
                consonants += 1
                j += 1

            # =========================
            # REGLAS DE CORTE
            # =========================
            if consonants == 1:
                syllables.append(word[start:i+1])
                start = i + 1

            elif consonants == 2:
                c1 = word[i + 1].lower()
                c2 = word[i + 2].lower()

                if SilabificadorFast.is_inseparable(c1, c2):
                    syllables.append(word[start:i+1])
                    start = i + 1
                else:
                    syllables.append(word[start:i+2])
                    start = i + 2
                    i += 1

            elif consonants > 2:
                syllables.append(word[start:i+2])
                start = i + 2
                i += 1

            i += 1

        # =========================
        # RESTO FINAL
        # =========================
        if start < length:
            syllables.append(word[start:])

        return syllables