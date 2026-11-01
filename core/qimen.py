"""奇门遁甲 (Qi Men Dun Jia) — simplified timing & accident analysis.
Uses 八门 (Eight Doors), 九星 (Nine Stars), 八神 (Eight Spirits)
for event timing and accident prediction."""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 八门 (Eight Doors) — represent different life domains
BA_MEN = {
    0: {"name": "休", "meaning": "休息,修养,安定", "element": "水", "type": "吉"},
    1: {"name": "生", "meaning": "生长,创造,财富", "element": "土", "type": "吉"},
    2: {"name": "伤", "meaning": "伤害,竞争,损失", "element": "木", "type": "凶"},
    3: {"name": "杜", "meaning": "堵塞,保密,隐藏", "element": "木", "type": "平"},
    4: {"name": "景", "meaning": "美景,娱乐,名声", "element": "火", "type": "平"},
    5: {"name": "死", "meaning": "死亡,结束,固定", "element": "土", "type": "凶"},
    6: {"name": "惊", "meaning": "惊恐,意外,官非", "element": "金", "type": "凶"},
    7: {"name": "开", "meaning": "开放,开始,成功", "element": "金", "type": "吉"},
}

# 九星 (Nine Stars)
JIU_XING = {
    0: {"name": "天蓬", "meaning": "胆大冒险,盗贼", "type": "凶"},
    1: {"name": "天芮", "meaning": "疾病,学生,问题", "type": "凶"},
    2: {"name": "天冲", "meaning": "冲击,震动,快速", "type": "平"},
    3: {"name": "天辅", "meaning": "辅助,教育,文化", "type": "吉"},
    4: {"name": "天禽", "meaning": "中央,稳定,中和", "type": "吉"},
    5: {"name": "天心", "meaning": "心思,医疗,策划", "type": "吉"},
    6: {"name": "天柱", "meaning": "破坏,批评,倒塌", "type": "凶"},
    7: {"name": "天任", "meaning": "担当,责任,勤劳", "type": "吉"},
    8: {"name": "天英", "meaning": "英明,名声,急躁", "type": "平"},
}

# 八神 (Eight Spirits)
BA_SHEN = {
    0: {"name": "值符", "meaning": "最吉,贵人,庇护", "type": "吉"},
    1: {"name": "腾蛇", "meaning": "虚惊,怪异,变化", "type": "凶"},
    2: {"name": "太阴", "meaning": "暗中,策划,女性", "type": "吉"},
    3: {"name": "六合", "meaning": "合作,婚姻,中介", "type": "吉"},
    4: {"name": "白虎", "meaning": "凶暴,血光,争斗", "type": "凶"},
    5: {"name": "玄武", "meaning": "偷盗,欺骗,隐私", "type": "凶"},
    6: {"name": "九地", "meaning": "稳定,迟缓,防守", "type": "吉"},
    7: {"name": "九天", "meaning": "高远,行动,进攻", "type": "吉"},
}

ACCIDENT_DOORS = ["伤", "死", "惊"]
ACCIDENT_STARS = ["天蓬", "天芮", "天冲", "天柱"]
ACCIDENT_SPIRITS = ["腾蛇", "白虎", "玄武"]


class QiMenEngine:
    def calculate(self, year, month, day, hour, lat=39.9, lng=116.4):
        """Calculate Qi Men Dun Jia pattern for a given date/time.
        Returns 八门, 九星, 八神 for accident analysis."""
        # Simplified calculation based on time
        # In practice, QMDJ requires detailed 局 calculation
        # Here we use a simplified 时家奇门 approach

        # Determine 旬首 and 符头 based on hour
        hour_period = (year + month + day + hour) % 9  # 9 局
        ju = hour_period % 9 or 9

        # Calculate 旬 (10-day period)
        xun = ((year * 365 + month * 28 + day + hour) % 60) // 10

        # Determine 值符 and 值使
        zhi_fu_idx = (hour + xun) % 9
        zhi_shi_idx = (month + day + hour) % 8

        # 八门
        door_info = BA_MEN.get(zhi_shi_idx % 8, BA_MEN[0])
        door = door_info["name"]

        # 九星
        star_info = JIU_XING.get(zhi_fu_idx % 9, JIU_XING[0])
        star = star_info["name"]

        # 八神 (determined by time)
        shen_idx = (hour // 2 + day) % 8
        shen_info = BA_SHEN.get(shen_idx, BA_SHEN[0])
        shen = shen_info["name"]

        # Accident analysis
        accident_indicators = []
        risk_score = 0

        if door in ACCIDENT_DOORS:
            idx = ACCIDENT_DOORS.index(door)
            severity = {0: 60, 1: 90, 2: 70}  # 伤=60, 死=90, 惊=70
            accident_indicators.append(f"八门{door}门: {BA_MEN[zhi_shi_idx%8]['meaning']}")
            risk_score += severity.get(idx, 50)

        if star in ACCIDENT_STARS:
            idx = ACCIDENT_STARS.index(star)
            severity = {0: 50, 1: 60, 2: 40, 3: 70}
            accident_indicators.append(f"九星{star}星: {JIU_XING[zhi_fu_idx%9]['meaning']}")
            risk_score += severity.get(idx, 30)

        if shen in ACCIDENT_SPIRITS:
            idx = ACCIDENT_SPIRITS.index(shen)
            severity = {0: 50, 1: 80, 2: 60}
            accident_indicators.append(f"八神{shen}: {BA_SHEN[shen_idx]['meaning']}")
            risk_score += severity.get(idx, 40)

        # Good spirits counteract
        if shen_info["type"] == "吉":
            risk_score = max(0, risk_score - 30)

        return {
            "ju": ju,
            "xun": xun,
            "door": {"name": door, "info": door_info},
            "star": {"name": star, "info": star_info},
            "spirit": {"name": shen, "info": shen_info},
            "accident_indicators": accident_indicators,
            "risk_score": min(100, risk_score),
            "overall": self._judge(door, star, shen),
        }

    def _judge(self, door, star, shen):
        """Overall judgment of the time's quality."""
        good_doors = {"休", "生", "开"}
        good_stars = {"天辅", "天禽", "天心", "天任"}
        good_spirits = {"值符", "太阴", "六合", "九地", "九天"}

        score = 50
        if door in good_doors:
            score += 15
        elif door in ACCIDENT_DOORS:
            score -= 20
        if star in good_stars:
            score += 10
        elif star in ACCIDENT_STARS:
            score -= 15
        if shen in good_spirits:
            score += 10
        elif shen in ACCIDENT_SPIRITS:
            score -= 15

        if score >= 70:
            return "吉"
        elif score >= 50:
            return "平"
        else:
            return "凶"

    def analyze_timing(self, birth_year, birth_month, birth_day, birth_hour):
        """Analyze the timing of a person's birth through QMDJ lens."""
        return self.calculate(birth_year, birth_month, birth_day, birth_hour)

    def analyze_death_window(self, birth_year, death_year, death_cause=None):
        """Analyze the death period for accident patterns."""
        # Check if death year QMDJ shows accident patterns
        result = self.calculate(death_year, 1, 1, 12)  # Approximate
        if death_cause:
            result["death_cause"] = death_cause
        return result
