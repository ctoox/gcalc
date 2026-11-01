"""Year-by-year 流年 (Fate Year) analysis engine.
For each year of life: compute 流年干支, 神煞, 冲克, event tendencies.
Critical for accident prediction, career timing, and life event matching."""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TIAN_GAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DI_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
WU_XING_GAN = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
WU_XING_ZHI = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}

# 神煞 - Annual Spirits (good and bad)
SHEN_SHA = {
    # Bad spirits (accident/disaster indicators)
    "天刑": {"conditions": [("申", "子", "辰"), "寅"], "type": "凶", "meaning": "刑罚官非,意外伤害"},
    "地煞": {"conditions": [("寅", "午", "戌"), "午"], "type": "凶", "meaning": "地陷灾难,跌打损伤"},
    "灾煞": {"conditions": [("申", "子", "辰"), "子"], "type": "凶", "meaning": "水火之灾,意外横祸"},
    "劫煞": {"conditions": [("巳", "酉", "丑"), "寅"], "type": "凶", "meaning": "劫夺盗窃,破财伤身"},
    "五鬼": {"conditions": [("亥", "卯", "未"), "卯"], "type": "凶", "meaning": "小人暗算,精神困扰"},
    "官符": {"conditions": [("寅", "午", "戌"), "辰"], "type": "凶", "meaning": "官非诉讼,口舌之争"},
    "丧门": {"conditions": [("寅", "午", "戌"), "寅"], "type": "凶", "meaning": "孝服丧事,亲人离别"},
    "吊客": {"conditions": [("寅", "午", "戌"), "戌"], "type": "凶", "meaning": "哀伤吊唁,病痛缠身"},
    "血刃": {"conditions": [("巳", "酉", "丑"), "午"], "type": "凶", "meaning": "血光之灾,手术外伤"},
    "大耗": {"conditions": [("亥", "卯", "未"), "未"], "type": "凶", "meaning": "破财损耗,投资失利"},
    # Good spirits
    "天德": {"conditions": [("亥", "卯", "未"), "亥"], "type": "吉", "meaning": "贵人相助,化解灾难"},
    "月德": {"conditions": [("寅", "午", "戌"), "丙"], "type": "吉", "meaning": "福星高照,逢凶化吉"},
    "天赦": {"conditions": [("寅", "午", "戌"), "寅"], "type": "吉", "meaning": "赦免罪过,绝处逢生"},
    "天乙": {"conditions": [("申", "子", "辰"), "子"], "type": "吉", "meaning": "贵人扶持,事业顺利"},
    "文昌": {"conditions": [("巳", "酉", "丑"), "酉"], "type": "吉", "meaning": "学业进步,文思敏捷"},
    "红鸾": {"conditions": [("寅", "午", "戌"), "卯"], "type": "吉", "meaning": "姻缘喜事,人缘旺盛"},
    "驿马": {"conditions": [("亥", "卯", "未"), "巳"], "type": "吉", "meaning": "动中求财,升迁远行"},
}

# 六冲 (Six Conflicts between branches)
LIU_CHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
             "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}

# 六合 (Six Harmonies)
LIU_HE = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
          "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}

# 三合 (Triple Harmonies)
SAN_HE = {
    ("申","子","辰"): "水局",
    ("亥","卯","未"): "木局",
    ("寅","午","戌"): "火局",
    ("巳","酉","丑"): "金局",
}

# 刑 (Punishments)
XING = {
    ("寅","巳"): "无恩之刑", ("巳","寅"): "无恩之刑",
    ("巳","申"): "无恩之刑", ("申","巳"): "无恩之刑",
    ("丑","未","戌"): "恃势之刑",
    ("子","卯"): "无礼之刑", ("卯","子"): "无礼之刑",
}

# Accident-related 流年 patterns
ACCIDENT_PATTERNS = [
    {"name": "岁运并临", "desc": "大运与流年干支相同,凶险之年"},
    {"name": "伤官见官", "desc": "流年伤官冲克年柱官星,官非口舌"},
    {"name": "枭神夺食", "desc": "流年枭神夺月令食神,意外伤病"},
    {"name": "羊刃倒戈", "desc": "流年羊刃冲克日主,血光之灾"},
    {"name": "日犯岁君", "desc": "流年地支冲日柱地支,本人灾祸"},
    {"name": "岁伤日干", "desc": "流年天干克日干,本人不顺"},
    {"name": "日犯岁君+岁伤日干", "desc": "天克地冲,大凶之年"},
]


def year_gan_zhi(year):
    """Get heavenly stem and earthly branch for a given year."""
    yg = (year - 4) % 10
    yz = (year - 4) % 12
    return TIAN_GAN[yg], DI_ZHI[yz]


def find_shen_sha(year_zhi):
    """Find active spirits for a given earthly branch."""
    active = {"吉": [], "凶": []}
    for name, info in SHEN_SHA.items():
        conds = info["conditions"]
        for cond in conds:
            if isinstance(cond, tuple):
                if year_zhi in cond:
                    active[info["type"]].append(name)
                    break
            elif isinstance(cond, str):
                # For 天干 conditions, check if the year's 天干 matches
                pass
    return active


def liu_chong(azhi, bzhi):
    """Check if two branches conflict."""
    return LIU_CHONG.get(azhi) == bzhi


def liu_he(azhi, bzhi):
    """Check if two branches harmonize."""
    return LIU_HE.get(azhi) == bzhi


def check_san_he(zhis):
    """Check if branches form a triple harmony."""
    for combo, name in SAN_HE.items():
        if all(z in zhis for z in combo):
            return name
    return None


class YearlyEngine:
    def __init__(self):
        pass

    def analyze_year(self, bazi_result, year, age):
        """Analyze a specific year in the person's life.
        bazi_result: output from BaziEngine.calculate()
        year: the calendar year to analyze
        age: the person's age in that year
        """
        yg, yz = year_gan_zhi(year)

        # Get the four pillars
        bazi_str = bazi_result.get("bazi", "")
        pillars = bazi_str.split() if bazi_str else ["","","",""]
        year_pillar = pillars[0] if len(pillars) > 0 else ""
        month_pillar = pillars[1] if len(pillars) > 1 else ""
        day_pillar = pillars[2] if len(pillars) > 2 else ""
        hour_pillar = pillars[3] if len(pillars) > 3 else ""

        year_gan = year_pillar[0] if len(year_pillar) > 0 else ""
        year_zhi = year_pillar[1] if len(year_pillar) > 1 else ""
        day_gan = day_pillar[0] if len(day_pillar) > 0 else ""
        day_zhi = day_pillar[1] if len(day_pillar) > 1 else ""
        month_zhi = month_pillar[1] if len(month_pillar) > 1 else ""

        dm_element = bazi_result.get("day_master_element", "")
        elements = bazi_result.get("elements", {})
        miss = elements.get("missing", [])

        # Conflicts
        conflicts = []
        if liu_chong(yz, day_zhi):
            conflicts.append("日犯岁君")
        if liu_chong(yz, year_zhi):
            conflicts.append("岁君冲年")
        if liu_chong(yz, month_zhi):
            conflicts.append("冲月令")

        # Heavenly stem conflicts
        day_gan_element = WU_XING_GAN.get(day_gan, "")
        yg_element = WU_XING_GAN.get(yg, "")
        if yg_element and day_gan_element:
            ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            if ke.get(yg_element) == day_gan_element:
                conflicts.append("岁伤日干")
            if ke.get(day_gan_element) == yg_element:
                conflicts.append("日干伤岁")

        # Harmonies
        harmonies = []
        if liu_he(yz, day_zhi):
            harmonies.append("与日支六合")
        if liu_he(yz, year_zhi):
            harmonies.append("与年支六合")

        # Triple harmony
        all_zhis = [z for z in [year_zhi, day_zhi, month_zhi, yz] if z]
        san_he = check_san_he(all_zhis)
        if san_he:
            harmonies.append(f"三合{san_he}")

        # Active spirits
        spirits = find_shen_sha(yz)

        # Event tendencies
        events = []
        accident_risk = 0

        # Accident signals
        if "日犯岁君" in conflicts and "岁伤日干" in conflicts:
            events.append("天克地冲: 本年大凶,易有意外")
            accident_risk += 40
        if "日犯岁君" in conflicts:
            events.append("日犯岁君: 个人重大变化年")
            accident_risk += 20
        if liu_chong(yz, year_zhi):
            events.append("冲年柱: 家族/长辈相关变动")
            accident_risk += 10
        if "灾煞" in spirits["凶"]:
            events.append("灾煞临门: 水火灾害风险")
            accident_risk += 25
        if "血刃" in spirits["凶"]:
            events.append("血刃照命: 血光外伤风险")
            accident_risk += 20
        if "天刑" in spirits["凶"]:
            events.append("天刑降临: 官非刑罚风险")
            accident_risk += 15
        if "丧门" in spirits["凶"] or "吊客" in spirits["凶"]:
            events.append("丧吊临门: 孝服病痛之年")
            accident_risk += 15
        if san_he and dm_element:
            # Triple harmony with the element that controls day master
            ke_map = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
            controlled_by = ke_map.get(dm_element, "")
            if controlled_by and san_he and controlled_by in san_he:
                events.append(f"{san_he}克日主({controlled_by}): 压力巨大")
                accident_risk += 15

        # Good signals
        if "天德" in spirits["吉"]:
            events.append("天德护身: 逢凶化吉")
            accident_risk = max(0, accident_risk - 15)
        if "月德" in spirits["吉"]:
            events.append("月德照命: 贵人相助")
            accident_risk = max(0, accident_risk - 10)
        if "天赦" in spirits["吉"]:
            events.append("天赦降临: 绝处逢生")
            accident_risk = max(0, accident_risk - 20)
        if "红鸾" in spirits["吉"]:
            events.append("红鸾星动: 姻缘喜事")
        if "驿马" in spirits["吉"]:
            events.append("驿马星动: 动中求财/迁居远行")
        if harmonies:
            events.append("六合化解: 有惊无险")

        # Element imbalance this year
        yg_el = WU_XING_GAN.get(yg, "")
        yz_el = WU_XING_ZHI.get(yz, "")
        year_els = {}
        if yg_el:
            year_els[yg_el] = year_els.get(yg_el, 0) + 1
        if yz_el:
            year_els[yz_el] = year_els.get(yz_el, 0) + 1

        # Fortune direction
        if yg_el and dm_element:
            ke_map = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            sheng_map = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
            if sheng_map.get(yg_el) == dm_element:
                events.append("流年生日主: 顺遂之年")
            elif ke_map.get(yg_el) == dm_element:
                events.append("流年克日主: 压力挑战年")

        return {
            "year": year,
            "age": age,
            "gan_zhi": f"{yg}{yz}",
            "year_gan": yg,
            "year_zhi": yz,
            "conflicts": conflicts,
            "harmonies": harmonies,
            "spirits_good": spirits["吉"],
            "spirits_bad": spirits["凶"],
            "accident_risk": accident_risk,
            "events": events,
            "year_elements": year_els,
            "accident_patterns": self._check_accident_patterns(bazi_result, year),
        }

    def _check_accident_patterns(self, bazi_result, year):
        """Check specific 命理 accident patterns."""
        patterns = []
        # Check day master and year
        for pat in ACCIDENT_PATTERNS:
            patterns.append({"name": pat["name"], "desc": pat["desc"], "active": False})
        return patterns

    def analyze_life(self, bazi_result, birth_year, death_year=None):
        """Analyze every year of the person's life.
        Returns timeline of year-by-year analysis."""
        now = 2026
        end_year = min(death_year or now, now)
        timeline = []
        for age, year in enumerate(range(birth_year, end_year + 1), start=1):
            if age > 120:
                break
            timeline.append(self.analyze_year(bazi_result, year, age))
        return timeline

    def find_death_years(self, timeline):
        """Identify years with highest accident/death risk."""
        high_risk = []
        for y in timeline:
            if y["accident_risk"] >= 50:
                high_risk.append({
                    "year": y["year"],
                    "age": y["age"],
                    "risk": y["accident_risk"],
                    "conflicts": y["conflicts"],
                    "spirits": y["spirits_bad"],
                    "events": y["events"],
                })
        return sorted(high_risk, key=lambda x: -x["risk"])

    def compare_death_year(self, timeline, death_year):
        """Analyze the actual death year specifically."""
        for y in timeline:
            if y["year"] == death_year:
                return y
        return None
