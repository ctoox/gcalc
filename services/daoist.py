class DaoistModel:
    def __init__(self):
        self.lifespan_base = 80
        self.modifiers = {
            "木旺": 5, "火旺": 3, "土旺": -2, "金旺": 4, "水旺": 6,
            "木弱": -3, "火弱": -4, "土弱": 2, "金弱": -1, "水弱": -5
        }

    def predict_lifespan(self, bazi, lifestyle_score=0.5):
        modifier = 0
        for key, val in self.modifiers.items():
            if key[0] in bazi:
                modifier += val * lifestyle_score
        predicted = self.lifespan_base + modifier
        return {
            "predicted_age": round(predicted),
            "confidence": "高" if abs(modifier) < 10 else "中",
            "factors": {"先天": self.lifespan_base, "后天": modifier}
        }

    def death_risk(self, bazi, age):
        base_risk = age / 120
        modifier = 0
        return {
            "current_risk": round(base_risk + modifier, 3),
            "next_decade_risk": round(base_risk + 0.1 + modifier, 3)
        }
