# =========================================================
# 🔹 MEMORY UNIT
# =========================================================
import time
class MemoryUnit:
    def __init__(self, content, confidence=0.5, origin=None):
        self.content = content
        self.confidence = confidence
        self.origin = origin

        self.frequency = 1
        self.last_access = time.time()
        self.state = "activa"

        # 🔥 embedding vectorial
        self.embedding = None

    def reinforce(self, value=0.1):
        self.confidence = min(1.0, self.confidence + value)
        self.frequency += 1
        self.last_access = time.time()

    def degrade(self, value=0.05):
        self.confidence = max(0.0, self.confidence - value)
        self.last_access = time.time()

        if self.confidence < 0.2:
            self.state = "descartada"
