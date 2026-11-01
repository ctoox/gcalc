class ScenarioAnalyzer:
    SCENARIOS = {
        "career": ["创业", "跳槽", "升职", "转行"],
        "love": ["表白", "分手", "结婚", "异地"],
        "finance": ["投资", "购房", "理财"]
    }

    def analyze(self, scenario_type, bazi, params=None):
        if scenario_type not in self.SCENARIOS:
            return {"error": f"未知场景: {scenario_type}"}
        return {
            "scenario": scenario_type,
            "timing": "吉" if params and params.get("month", 1) % 2 == 1 else "待机",
            "recommendation": "顺势而为",
            "alternatives": self.SCENARIOS[scenario_type]
        }

    def full_analysis(self, bazi, scenarios=None):
        if scenarios is None:
            scenarios = list(self.SCENARIOS.keys())
        return {s: self.analyze(s, bazi) for s in scenarios}
