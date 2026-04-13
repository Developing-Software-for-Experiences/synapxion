class BpeTokenizer:
    def __init__(self, merge_rules):
        # 🔥 Normalizar reglas al inicializar (clave para rendimiento)
        self.merge_rules = []
        
        for rule in (merge_rules or []):
            parsed = self._parse_rule(rule)
            if parsed:
                self.merge_rules.append(parsed)

    # =========================
    # 🔹 PARSE SEGURO DE REGLAS
    # =========================
    def _parse_rule(self, rule):
        try:
            if isinstance(rule, dict):
                left = rule.get("left") or rule.get("Item1")
                right = rule.get("right") or rule.get("Item2")
                merged = rule.get("merged") or rule.get("Item3")

            elif isinstance(rule, (list, tuple)) and len(rule) >= 3:
                left, right, merged = rule[0], rule[1], rule[2]

            else:
                return None

            # 🔥 Validación extra
            if left is None or right is None or merged is None:
                return None

            return (left, right, merged)

        except Exception:
            return None

    # =========================
    # 🔹 APLICAR BPE
    # =========================
    def apply(self, tokens):
        if not self.merge_rules or not tokens:
            return tokens

        result = list(tokens)

        # 🔥 Aplicar reglas en orden (como BPE real)
        for left, right, merged in self.merge_rules:

            i = 0
            new_result = []

            while i < len(result):
                # 🔹 match de par
                if i < len(result) - 1 and result[i] == left and result[i + 1] == right:
                    new_result.append(merged)
                    i += 2  # saltar ambos
                else:
                    new_result.append(result[i])
                    i += 1

            result = new_result

        return result