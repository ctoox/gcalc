class DataValidator:
    def validate_person(self, data):
        errors = []
        if not data.get("name"):
            errors.append("姓名不能为空")
        if not data.get("birth_year") or data["birth_year"] < 1900:
            errors.append("出生年份无效")
        if data.get("birth_year", 2026) > 2026:
            errors.append("出生年份不能晚于当前年份")
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_bazi(self, bazi_str):
        if len(bazi_str) != 4:
            return {"valid": False, "reason": "八字必须为4个字符"}
        return {"valid": True, "bazi": bazi_str}

    def validate_api_input(self, data, required_fields):
        missing = [f for f in required_fields if f not in data]
        if missing:
            return {"valid": False, "missing": missing}
        return {"valid": True}
