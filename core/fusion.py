"""
Fusion Engine: combines BaZi (Chinese) + Western astrology + Numerology.
Provides a unified destiny analysis.
"""

from core.bazi import BaziEngine
from core.western import WesternEngine
from core.relationship import RelationshipEngine
from datetime import date

class FusionEngine:
    def __init__(self):
        self.bazi = BaziEngine()
        self.western = WesternEngine()
        self.relationship = RelationshipEngine()

    def analyze_person(self, birth_year, birth_month, birth_day, birth_hour=12,
                       name="", gender="男", family_rank=2, birth_order=1):
        """Full combined analysis of a person"""
        bazi_result = self.bazi.calculate(birth_year, birth_month, birth_day, birth_hour)
        birth_date = date(birth_year, birth_month, birth_day)
        western_result = self.western.calculate_chart(birth_date, birth_hour)
        numerology = self.western.numerology(birth_date)
        fortune_cycles = self.bazi.fortune_cycles(birth_year, gender)

        zodiac_idx = (birth_year - 4) % 12
        zodiac_names = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake","Horse","Goat","Monkey","Rooster","Dog","Pig"]
        zodiac = zodiac_names[zodiac_idx]

        fusion_score = self._fusion_score(bazi_result, western_result, numerology)

        career_intersection = self._career_intersection(
            bazi_result.get("career_affinity", []),
            western_result.get("career_hints", [])
        )

        return {
            "name": name,
            "birth": f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
            "gender": gender,
            "chinese": {
                "bazi": bazi_result.get("bazi", ""),
                "four_pillars": bazi_result.get("four_pillars", {}),
                "day_master": bazi_result.get("day_master", ""),
                "day_master_element": bazi_result.get("day_master_element", ""),
                "elements": bazi_result.get("elements", {}),
                "zodiac": zodiac,
                "personality": bazi_result.get("personality", ""),
                "career_affinity": bazi_result.get("career_affinity", []),
                "wealth_potential": bazi_result.get("wealth_potential", {}),
                "fortune_cycles": fortune_cycles,
                "hidden_stems": bazi_result.get("hidden_stems", []),
            },
            "western": {
                "sun_sign": western_result.get("sun_sign", ""),
                "sun_sign_en": western_result.get("sun_sign_en", ""),
                "moon_sign": western_result.get("moon_sign", ""),
                "rising_sign": western_result.get("rising_sign", ""),
                "element": western_result.get("element", ""),
                "modality": western_result.get("modality", ""),
                "ruler_planet": western_result.get("ruler_planet", ""),
                "element_balance": western_result.get("element_balance", {}),
                "dominant_element": western_result.get("dominant_element", ""),
                "personality": western_result.get("personality", ""),
                "career_hints": western_result.get("career_hints", []),
            },
            "numerology": numerology,
            "fusion": {
                "bazi_element": bazi_result.get("day_master_element", ""),
                "sun_sign_element": western_result.get("element", ""),
                "dominant_astrology_element": western_result.get("dominant_element", ""),
                "east_west_harmony": self._east_west_harmony(
                    bazi_result.get("day_master_element", ""),
                    western_result.get("element", "")
                ),
                "career_intersection": career_intersection,
                "overall_score": fusion_score,
                "recommendation": self._recommendation(fusion_score),
            },
            "family": self.relationship.family_environment_analysis(
                self._make_person_obj(name, birth_year, birth_month, birth_day,
                                      birth_hour, bazi_result, family_rank, birth_order)
            ),
        }

    def _make_person_obj(self, name, y, m, d, h, bazi, rank, order):
        class PersonProxy:
            pass
        p = PersonProxy()
        p.name = name
        p.birth_year = y
        p.birth_month = m
        p.birth_day = d
        p.birth_hour = h
        p.family_rank = rank
        p.birth_order = order
        p.family_wealth = ""
        p._bazi_cache = bazi
        return p

    def _east_west_harmony(self, bazi_element, sun_element):
        """Compare Chinese WuXing element with Western element"""
        wuxing_to_western = {"木": ["风"], "火": ["火"], "土": ["土"], "金": ["风","土"], "水": ["水"]}
        western_to_wuxing = {"火": "火", "土": "土", "风": "木", "水": "水"}
        west_wuxing = western_to_wuxing.get(sun_element, "")

        if bazi_element == west_wuxing:
            return "同元素, 东西方高度一致 (+30)"
        elif west_wuxing and (bazi_element, west_wuxing) in [("木","水"),("火","木"),("土","火"),("金","土"),("水","金")]:
            return "相生关系, 东西方互有增益 (+20)"
        elif west_wuxing and (bazi_element, west_wuxing) in [("木","金"),("火","水"),("土","木"),("金","火"),("水","土")]:
            return "相克关系, 东西方需平衡 (-10)"
        return "中性, 无显著冲突 (+10)"

    def _career_intersection(self, chinese_careers, western_careers):
        """Find career suggestions that overlap between East and West"""
        chinese_set = set(chinese_careers)
        western_set = set(western_careers)
        intersection = chinese_set & western_set
        union = chinese_set | western_set
        return {
            "top_matches": sorted(intersection, key=lambda x: chinese_careers.index(x)) if intersection else [],
            "chinese_only": sorted(chinese_set - western_set),
            "western_only": sorted(western_set - chinese_set),
            "all_options": sorted(union),
        }

    def _fusion_score(self, bazi, western, numerology):
        """Combined score across all systems"""
        score = 50

        day_master = bazi.get("day_master_element", "")
        dominant_element = western.get("dominant_element", "")
        west_to_east = {"火": "火", "土": "土", "风": "木", "水": "水"}
        west_element = west_to_east.get(dominant_element, "")

        if day_master and west_element:
            if day_master == west_element:
                score += 20
            elif (day_master, west_element) in [("木","水"),("火","木"),("土","火"),("金","土"),("水","金")]:
                score += 15
            else:
                score -= 5

        wealth = bazi.get("wealth_potential", {}).get("score", 50)
        score += (wealth - 50) * 0.2

        if "missing" in bazi.get("elements", {}):
            missing = bazi["elements"]["missing"]
            if len(missing) <= 1:
                score += 10
            elif len(missing) >= 3:
                score -= 10

        life_path = numerology.get("life_path", 5)
        if life_path in [1, 3, 5, 8]:
            score += 5
        elif life_path in [4, 7]:
            score += 3

        return max(0, min(100, round(score)))

    def _recommendation(self, score):
        if score >= 80:
            return "命格极佳, 东西方命理高度统一, 宜全力发展"
        elif score >= 65:
            return "命格上等, 东西方相互补益, 顺势而为即可"
        elif score >= 45:
            return "命格中等, 有潜力有挑战, 需扬长避短"
        else:
            return "命格需修炼, 东西方有冲突, 宜稳中求进"

    def analyze_mentor_relation(self, protege_info, mentor_info):
        """Analyze how a mentor/benefactor influenced a protege's fate"""
        protege_bazi = self.bazi.calculate(
            protege_info["birth_year"], protege_info["birth_month"],
            protege_info["birth_day"], protege_info.get("birth_hour", 12)
        )
        mentor_bazi = self.bazi.calculate(
            mentor_info["birth_year"], mentor_info["birth_month"],
            mentor_info["birth_day"], mentor_info.get("birth_hour", 12)
        )

        comp = self.relationship.analyze_mentor(protege_bazi, mentor_bazi)

        protege_fortune = self.bazi.annual_fortune(
            protege_info["birth_year"], protege_info["birth_month"],
            protege_info["birth_day"], mentor_info.get("met_year", 1900)
        )

        return {
            "protege": protege_info["name"],
            "mentor": mentor_info["name"],
            "mentor_bazi": mentor_bazi.get("bazi", ""),
            "mentor_element": mentor_bazi.get("day_master_element", ""),
            "compatibility": comp,
            "meeting_year_fortune": protege_fortune,
            "summary": f"{protege_info['name']}遇{mentor_info['name']}: "
                       f"缘分配对{comp['score']}分, 师父五行{mentor_bazi.get('day_master_element','')}, "
                       f"{'大吉' if comp['is_beneficial'] else '普通'}之遇"
        }
