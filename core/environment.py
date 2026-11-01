class EnvironmentEngine:
    FACTORS = ["地域", "气候", "家庭", "教育", "社会"]

    def analyze(self, birth_info, location=None):
        return {
            "environment_score": 0.75,
            "factors": {
                "geography": {"score": 0.8, "note": "东方木旺"},
                "climate": {"score": 0.7, "note": "四季分明"},
                "family": {"score": 0.75, "note": "书香门第"},
            },
            "derivation": "环境推导: 木火通明之象"
        }

    def compare_environments(self, env_a, env_b):
        return {"compatibility": 0.85, "synergy": "相辅相成"}
