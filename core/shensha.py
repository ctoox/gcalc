class ShenshaEngine:
    SHEN_SHA = {
        "天乙贵人": "贵人相助，逢凶化吉",
        "文昌": "聪明好学，文采出众",
        "桃花": "异性缘佳，感情丰富",
    }

    def lookup(self, bazi):
        results = []
        if "甲" in bazi or "戊" in bazi:
            results.append({"name": "天乙贵人", "meaning": self.SHEN_SHA["天乙贵人"]})
        return results
