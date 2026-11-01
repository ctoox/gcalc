class ScienceHealthModel:
    def __init__(self):
        self.framingham_cohort = {
            "male": {"baseline": 0.1, "age_coeff": 0.05},
            "female": {"baseline": 0.08, "age_coeff": 0.04}
        }

    def framingham_risk(self, profile):
        gender = profile.get("gender", "male")
        age = profile.get("age", 50)
        coeffs = self.framingham_cohort.get(gender, self.framingham_cohort["male"])
        risk = coeffs["baseline"] + coeffs["age_coeff"] * (age - 40) / 10
        risk += profile.get("cholesterol", 200) * 0.001
        risk -= profile.get("hdl", 50) * 0.002
        return {
            "ten_year_risk": round(min(risk, 1), 3),
            "risk_category": "高" if risk > 0.2 else "中" if risk > 0.1 else "低"
        }

    def bmi_health(self, weight_kg, height_cm):
        bmi = weight_kg / ((height_cm / 100) ** 2)
        category = "正常"
        if bmi < 18.5:
            category = "偏瘦"
        elif bmi >= 24:
            category = "偏胖"
        elif bmi >= 28:
            category = "肥胖"
        return {"bmi": round(bmi, 1), "category": category}
