class MatchingEngine:
    def __init__(self):
        self.celebrities = []

    def load_data(self, db):
        self.celebrities = db.query("SELECT * FROM persons WHERE category = 'celebrity'")

    def find_matches(self, bazi, limit=10):
        matches = []
        for celeb in self.celebrities[:limit]:
            score = self._similarity(bazi, celeb["bazi"] if "bazi" in celeb else "")
            matches.append({"name": celeb["name"], "score": score})
        return sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]

    def _similarity(self, bazi_a, bazi_b):
        if not bazi_a or not bazi_b:
            return 0
        same = sum(1 for a, b in zip(bazi_a, bazi_b) if a == b)
        return same * 100 / max(len(bazi_a), len(bazi_b), 1)
