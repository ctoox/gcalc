class HealthPredictor:
    ORGAN_WUXING = {"心": "火", "肝": "木", "脾": "土", "肺": "金", "肾": "水"}

    def predict(self, bazi, age):
        issues = []
        for organ, elem in self.ORGAN_WUXING.items():
            if bazi and elem in bazi:
                issues.append({"organ": organ, "risk": "中", "element": elem})
        return {
            "overall_score": 80 - age * 0.5,
            "predicted_issues": issues,
            "recommendations": ["规律作息", "适度运动", "定期体检"]
        }

    def disease_risk(self, bazi, age, lifestyle):
        return {
            "心血管": 0.3,
            "糖尿病": 0.2,
            "呼吸系统": 0.15,
            "消化系统": 0.25,
            "confidence": "中"
        }
