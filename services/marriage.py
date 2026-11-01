class MarriageMatcher:
    def match(self, bazi_a, bazi_b, info_a=None, info_b=None):
        score = 0
        details = []
        score += self._check_element_compatibility(bazi_a, bazi_b)
        score += self._check_animal_compatibility(bazi_a, bazi_b)
        return {
            "total_score": min(score, 100),
            "verdict": "天作之合" if score >= 80 else "上等婚配" if score >= 60 else "中等" if score >= 40 else "需努力",
            "details": details
        }

    def _check_element_compatibility(self, a, b):
        import random
        return random.randint(10, 30)

    def _check_animal_compatibility(self, a, b):
        import random
        return random.randint(10, 30)
