import json
import os

class DataVerifier:
    def __init__(self, data_path="data"):
        self.data_path = data_path

    def verify_json(self, filename):
        path = os.path.join(self.data_path, filename)
        if not os.path.exists(path):
            return {"valid": False, "error": f"文件不存在: {path}"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"valid": True, "count": len(data) if isinstance(data, list) else 1}
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"JSON解析错误: {e}"}

    def verify_person(self, person):
        required = ["name", "birth_year", "birth_month", "birth_day"]
        missing = [f for f in required if f not in person]
        if missing:
            return {"valid": False, "missing": missing}
        if person["birth_year"] < 1800 or person["birth_year"] > 2026:
            return {"valid": False, "error": "出生年份超出合理范围"}
        return {"valid": True}

if __name__ == "__main__":
    verifier = DataVerifier()
    result = verifier.verify_json("collected_data.json")
    print(f"Verification: {result}")
