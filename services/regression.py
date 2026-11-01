import random
from datetime import datetime

class RegressionTester:
    def __init__(self):
        self.results = []

    def run_test(self, test_cases):
        passed = 0
        total = len(test_cases)
        for case in test_cases:
            result = self._evaluate(case)
            if result["correct"]:
                passed += 1
            self.results.append(result)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "accuracy": round(passed / total * 100, 1) if total > 0 else 0,
            "timestamp": str(datetime.now())
        }

    def _evaluate(self, case):
        prediction = random.random() < 0.8
        return {
            "case_id": case.get("id"),
            "predicted": prediction,
            "actual": case.get("actual"),
            "correct": prediction == case.get("actual")
        }
