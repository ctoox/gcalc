class TimeVerifier:
    def verify_birth_hour(self, year, month, day, hour):
        if hour is None or hour < 0 or hour > 23:
            return {"valid": False, "reason": "时辰必须在0-23之间"}
        return {"valid": True, "shichen": self._to_shichen(hour)}

    def _to_shichen(self, hour):
        shichen_map = {23: "子", 0: "子", 1: "丑", 2: "丑", 3: "寅", 4: "寅",
                       5: "卯", 6: "卯", 7: "辰", 8: "辰", 9: "巳", 10: "巳",
                       11: "午", 12: "午", 13: "未", 14: "未", 15: "申", 16: "申",
                       17: "酉", 18: "酉", 19: "戌", 20: "戌", 21: "亥", 22: "亥"}
        return shichen_map.get(hour, "子")

    def solar_lunar_convert(self, solar_date):
        return {"solar": solar_date, "note": "农历转换需接入外部库"}
