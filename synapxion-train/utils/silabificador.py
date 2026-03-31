# utils/silabificador.py

class Silabificador:

    VOWELS = set("aeiouáéíóúü")
    STRONG_VOWELS = set("aáeéoó")
    WEAK_VOWELS = set("iíuúü")

    INSEPARABLE_GROUPS = {
        "br", "bl", "cr", "cl", "dr",
        "fr", "fl", "gr", "gl",
        "pr", "pl", "tr"
    }

    @staticmethod
    def is_vowel(c):
        return c in Silabificador.VOWELS

    @staticmethod
    def is_strong(c):
        return c in Silabificador.STRONG_VOWELS

    @staticmethod
    def is_weak(c):
        return c in Silabificador.WEAK_VOWELS

    @staticmethod
    def has_accent(c):
        return c in "áéíóú"

    # ------------------------
    # SPLIT INTO SYLLABLES
    # ------------------------
    @staticmethod
    def split_into_syllables(word):
        syllables = []
        current = []

        word = word.lower()
        i = 0
        length = len(word)

        while i < length:
            current.append(word[i])

            if Silabificador.is_vowel(word[i]):
                next_idx = i + 1

                # 🔹 HIATO / DIPTONGO
                if next_idx < length and Silabificador.is_vowel(word[next_idx]):
                    v1 = word[i]
                    v2 = word[next_idx]

                    hiato = (
                        (Silabificador.is_strong(v1) and Silabificador.is_strong(v2)) or
                        (Silabificador.is_strong(v1) and Silabificador.is_weak(v2) and Silabificador.has_accent(v2)) or
                        (Silabificador.is_weak(v1) and Silabificador.is_strong(v2) and Silabificador.has_accent(v1))
                    )

                    if not hiato:
                        # Diptongo → no cortar
                        current.append(word[next_idx])
                        i += 1

                # 🔹 CONTAR CONSONANTES
                consonant_count = 0
                j = i + 1

                while j < length and not Silabificador.is_vowel(word[j]):
                    consonant_count += 1
                    j += 1

                if consonant_count == 1:
                    syllables.append("".join(current))
                    current = []

                elif consonant_count == 2:
                    group = word[i+1:i+3]

                    if group in Silabificador.INSEPARABLE_GROUPS:
                        syllables.append("".join(current))
                        current = []
                    else:
                        current.append(word[i+1])
                        syllables.append("".join(current))
                        current = []
                        i += 1

                elif consonant_count > 2:
                    current.append(word[i+1])
                    syllables.append("".join(current))
                    current = []
                    i += 1

            i += 1

        if current:
            syllables.append("".join(current))

        return syllables

    # ------------------------
    # JOIN SYLLABLES
    # ------------------------
    @staticmethod
    def join_syllables(syllables):
        if not syllables:
            return ""
        return "".join(syllables)




