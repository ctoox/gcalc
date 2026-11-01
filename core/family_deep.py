"""Deep family environment analysis.
Chinese celebrity records often hide the truth — family environment
shapes personality which shapes destiny.
Analyzes: parent compatibility, childhood conditions, hidden influences."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi import BaziEngine
from datetime import date

ELEMENTS = ["金", "木", "水", "火", "土"]
SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}

class FamilyDeepAnalyzer:
    def __init__(self):
        self.bazi = BaziEngine()

    def analyze(self, bazi_result, birth_year, gender="男", family_secrets=""):
        """Deep family environment analysis.
        family_secrets: any known hidden information about the person's background.
        """
        dm = bazi_result.get("day_master_element", "")
        bazi_str = bazi_result.get("bazi", "")
        pillars = bazi_str.split() if bazi_str else ["","","",""]
        year_pillar = pillars[0] if len(pillars) > 0 else ""
        month_pillar = pillars[1] if len(pillars) > 1 else ""
        day_pillar = pillars[2] if len(pillars) > 2 else ""
        hour_pillar = pillars[3] if len(pillars) > 3 else ""

        year_gan = year_pillar[0] if len(year_pillar) > 0 else ""
        year_zhi = year_pillar[1] if len(year_pillar) > 1 else ""
        month_gan = month_pillar[0] if len(month_pillar) > 0 else ""
        month_zhi = month_pillar[1] if len(month_pillar) > 1 else ""
        day_gan = day_pillar[0] if len(day_pillar) > 0 else ""
        day_zhi = day_pillar[1] if len(day_pillar) > 1 else ""

        el_counts = bazi_result.get("elements", {}).get("counts", {})
        miss = bazi_result.get("elements", {}).get("missing", [])

        # === Parent analysis (年柱 = parents, 月柱 = siblings) ===
        year_el = bazi_result.get("wuxing_gan", {}).get(year_gan, "") if hasattr(bazi_result, 'get') else ""
        parent_el = self._branch_element(year_zhi)

        # Parent compatibility with child's day master
        parent_relationship = self._element_relationship(parent_el, dm) if parent_el else "未知"

        # === Sibling analysis (月柱) ===
        sibling_el = self._branch_element(month_zhi) if month_zhi else ""
        sibling_relation = self._element_relationship(sibling_el, dm) if sibling_el else "未知"

        # === Childhood environment clues ===
        # Year branch gives childhood condition
        childhood_score = self._childhood_score(year_zhi, dm, el_counts)

        # === Hidden family secrets detection ===
        hidden_clues = self._detect_hidden(year_pillar, month_pillar, day_pillar, el_counts, miss)

        # === Wealth/poverty clues from family ===
        family_wealth = self._family_wealth(year_gan, year_zhi, dm, el_counts)

        # === Social mobility ===
        mobility = self._social_mobility(el_counts, dm, year_zhi)

        # === Personality formation from family ===
        personality_formation = self._personality_formation(dm, parent_el, sibling_el, childhood_score, miss)

        result = {
            "day_master": dm,
            "bazi": bazi_str,
            # Parent
            "parent_year_zhi": year_zhi,
            "parent_element": parent_el or "?",
            "parent_relationship_to_dm": parent_relationship,
            "parent_analysis": self._parent_text(parent_relationship, year_zhi),
            # Sibling
            "sibling_month_zhi": month_zhi,
            "sibling_element": sibling_el or "?",
            "sibling_relationship": sibling_relation,
            # Childhood
            "childhood_score": childhood_score,
            "childhood_description": self._childhood_text(childhood_score),
            # Hidden
            "hidden_clues": hidden_clues,
            "family_secrets_known": family_secrets or "无",
            # Socioeconomic
            "family_wealth": family_wealth,
            "social_mobility": mobility,
            # Personality formation
            "personality_formation": personality_formation,
            "nurture_effect": self._nurture_effect(miss, el_counts, dm),
        }
        return result

    def _branch_element(self, zhi):
        mapping = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土",
                   "巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
        return mapping.get(zhi, "")

    def _element_relationship(self, el1, el2):
        if el1 == el2:
            return "相同"
        if SHENG.get(el1) == el2:
            return "生我"
        if SHENG.get(el2) == el1:
            return "我生"
        if KE.get(el1) == el2:
            return "克我"
        if KE.get(el2) == el1:
            return "我克"
        return "无关"

    def _childhood_score(self, year_zhi, dm, el_counts):
        score = 50
        # Year branch quality
        good_zhi = {"寅","卯","巳","午","申","酉","亥"}
        bad_zhi = {"子","丑","辰","未","戌"}
        if year_zhi in good_zhi:
            score += 10
        elif year_zhi in bad_zhi:
            score -= 5
        # DM strength
        if el_counts.get(dm, 0) >= 2:
            score += 10
        elif el_counts.get(dm, 0) <= 1:
            score -= 10
        return max(0, min(100, score))

    def _detect_hidden(self, year_p, month_p, day_p, el_counts, miss):
        """Detect signs that family records may hide the truth."""
        clues = []
        # 年柱空亡 or 伏吟 suggests hidden family history
        if year_p and day_p and year_p == day_p:
            clues.append("年日伏吟: 祖上根基隐情")
        # Missing element that should be present
        if len(miss) >= 2:
            clues.append("缺二行以上: 家庭环境可能极端")
        # Extreme element imbalance
        if el_counts and max(el_counts.values(), default=0) >= 4:
            dominant = max(el_counts, key=el_counts.get)
            clues.append(f"{dominant}过旺: 家庭某方面过度影响")
        if not clues:
            clues.append("无明显隐藏迹象")
        return clues

    def _family_wealth(self, year_gan, year_zhi, dm, el_counts):
        """Estimate family wealth from childhood clues."""
        score = 30
        # 财星 in year pillar = family wealth
        cai = {"木":"土","火":"金","土":"水","金":"木","水":"火"}
        dm_cai = cai.get(dm, "")
        year_el = self._branch_element(year_zhi)
        if year_el == dm_cai:
            score += 30
        # DM strong = can manage family wealth
        if el_counts.get(dm, 0) >= 2:
            score += 20
        if len(el_counts) >= 4:
            score += 20
        if score >= 70:
            return "富裕"
        elif score >= 45:
            return "中等"
        else:
            return "贫寒"

    def _social_mobility(self, el_counts, dm, year_zhi):
        """Social mobility: how much the person rises above their birth."""
        score = 50
        dm_power = el_counts.get(dm, 0) if dm else 0
        if dm_power >= 3:
            score += 25
        elif dm_power >= 2:
            score += 10
        if year_zhi in {"子","丑","辰","戌","未"}:
            score -= 10  # Harder start
        if score >= 70:
            return "高"
        elif score >= 45:
            return "中"
        else:
            return "低"

    def _personality_formation(self, dm, parent_el, sibling_el, childhood, miss):
        """How family environment shapes personality."""
        traits = []
        # Parent influence
        if parent_el == dm:
            traits.append("继承父母性格特质明显")
        elif parent_el and KE.get(parent_el) == dm:
            traits.append("父母管教严格,形成坚韧性格")
        elif parent_el and SHENG.get(parent_el) == dm:
            traits.append("父母滋养支持,性格温和自信")

        # Childhood
        if childhood >= 70:
            traits.append("童年幸福,性格阳光开朗")
        elif childhood <= 30:
            traits.append("童年逆境,性格坚韧独立或敏感多思")

        # Missing elements
        if miss:
            traits.append(f"缺{''.join(miss)}: 成长中此方面需求未被满足")

        return traits if traits else ["性格形成无明显家庭印记"]

    def _nurture_effect(self, miss, el_counts, dm):
        """How much nurture (vs nature) affects this person's destiny."""
        # More missing elements = more nurture matters
        if len(miss) >= 2:
            return "高: 家庭环境对命格影响大于先天"
        if el_counts and max(el_counts.values(), default=0) >= 4:
            return "中: 先天某元素过旺,环境影响有限"
        return "中: 先天后天均衡影响"

    def _parent_text(self, relationship, zhi):
        texts = {
            "相同": f"父母与命主五行相同,性格相似,家庭和谐但有固执倾向",
            "生我": f"父母生助命主,家庭支持充足,有福荫",
            "我生": f"命主反生父母,早年可能承担家庭责任",
            "克我": f"父母约束较大,家教严格,或家庭压力大",
            "我克": f"命主克父母,父母依仗,或早年独立",
        }
        return texts.get(relationship, f"父母宫{zhi},关系一般")

    def _childhood_text(self, score):
        if score >= 70:
            return "幸福童年,家庭环境良好"
        elif score >= 45:
            return "童年平顺,有快乐也有挑战"
        else:
            return "童年艰辛,家庭环境不利成长"
