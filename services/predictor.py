class Predictor:
    def __init__(self):
        self.ten_year_cycles = 8

    def predict_major_fortune(self, bazi, start_age):
        cycles = []
        for i in range(self.ten_year_cycles):
            age_start = start_age + i * 10
            cycles.append({
                "age_range": f"{age_start}-{age_start + 9}",
                "element": ["木", "火", "土", "金", "水"][i % 5],
                "score": 80 - i * 5,
                "description": f"第{i+1}步大运"
            })
        return {"cycles": cycles, "total_cycles": len(cycles)}

    def predict_year(self, bazi, year):
        return {
            "year": year,
            "fortune": "吉" if year % 2 == 0 else "凶",
            "key_aspects": ["事业", "财运"],
            "warning": "注意投资风险" if year % 3 == 0 else None
        }
