import random

class YijingEngine:
    HEXAGRAMS = {
        1: ("乾", "天行健，君子以自强不息"),
        2: ("坤", "地势坤，君子以厚德载物"),
    }

    def divine(self, question=None):
        upper = random.randint(1, 8)
        lower = random.randint(1, 8)
        hex_num = upper * 8 + lower
        name, desc = self.HEXAGRAMS.get(1, ("乾", "天行健"))
        return {
            "hexagram": hex_num,
            "name": name,
            "description": desc,
            "changing_lines": self._get_changing_lines()
        }

    def _get_changing_lines(self):
        return [i for i in range(6) if random.random() < 0.5]
