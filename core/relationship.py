from core.bazi import BaziEngine

class RelationshipEngine:
    def __init__(self):
        self.bazi = BaziEngine()

    def analyze_compatibility(self, bazi_a, bazi_b):
        """Full BaZi compatibility between two people"""
        if isinstance(bazi_a, str):
            bazi_a = {"bazi": bazi_a}
        if isinstance(bazi_b, str):
            bazi_b = {"bazi": bazi_b}

        pillar_a = bazi_a.get("bazi", "")
        pillar_b = bazi_b.get("bazi", "")

        elements_a = bazi_a.get("elements", {}).get("counts", {})
        elements_b = bazi_b.get("elements", {}).get("counts", {})

        dm_a = bazi_a.get("day_master_element", "")
        dm_b = bazi_b.get("day_master_element", "")

        score = 0
        aspects = []

        if dm_a and dm_b:
            generating = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
            controlling = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            if generating.get(dm_a) == dm_b:
                score += 30
                aspects.append(f"五行相生: {dm_a}生{dm_b} (+30)")
            elif generating.get(dm_b) == dm_a:
                score += 25
                aspects.append(f"五行相生: {dm_b}生{dm_a} (+25)")
            if dm_a == dm_b:
                score += 15
                aspects.append(f"同五行: {dm_a} (+15)")

        # Element complement
        for elem in ["木","火","土","金","水"]:
            ea = elements_a.get(elem, 0)
            eb = elements_b.get(elem, 0)
            if (ea >= 2 and eb == 0) or (eb >= 2 and ea == 0):
                score += 10
                aspects.append(f"五行互补: {elem} (+10)")
                break

        # Hidden stem matching
        hidden_a = set(bazi_a.get("hidden_stems", []))
        hidden_b = set(bazi_b.get("hidden_stems", []))
        common = hidden_a & hidden_b
        if common:
            score += min(len(common) * 5, 15)
            aspects.append(f"藏干相通: {','.join(common)} (+{min(len(common)*5,15)})")

        pillar_score = 0
        for ca, cb in zip(pillar_a[:4], pillar_b[:4]):
            if ca == cb:
                pillar_score += 5
        if pillar_score > 0:
            score += pillar_score
            aspects.append(f"柱中同字: +{pillar_score}")

        level = "上等" if score >= 70 else "中等" if score >= 40 else "普通"
        return {
            "score": min(100, score),
            "level": level,
            "aspects": aspects,
            "summary": f"缘分配对评分{min(100,score)}分: {level}",
        }

    def analyze_mentor(self, protege_bazi, mentor_bazi):
        """Analyze if a mentor is beneficial for a protege"""
        comp = self.analyze_compatibility(protege_bazi, mentor_bazi)

        protege_day = protege_bazi.get("day_master_element", "")
        mentor_day = mentor_bazi.get("day_master_element", "")
        missing = protege_bazi.get("elements", {}).get("missing", [])
        mentor_elements = mentor_bazi.get("elements", {}).get("counts", {})

        mentor_fills_gap = False
        for m in missing:
            if mentor_elements.get(m, 0) >= 1:
                mentor_fills_gap = True
                break

        mentor_score = comp["score"]
        if mentor_fills_gap:
            mentor_score += 20
            comp["aspects"].append(f"师父补八字所缺: +20")

        comp["mentor_score"] = min(100, mentor_score)
        comp["is_beneficial"] = mentor_score >= 50
        comp["mentor_element"] = mentor_day
        comp["fills_gap"] = mentor_fills_gap

        return comp

    def analyze_team(self, members):
        """Analyze a team/group of people - find the best mentor figure"""
        results = []
        for i, m1 in enumerate(members):
            for j, m2 in enumerate(members):
                if i >= j:
                    continue
                comp = self.analyze_compatibility(m1["bazi"], m2["bazi"])
                results.append({
                    "pair": f"{m1['name']}-{m2['name']}",
                    "score": comp["score"],
                    "level": comp["level"],
                })
        results.sort(key=lambda x: -x["score"])
        return results

    def match_elements(self, elem_a, elem_b):
        cycle = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        if cycle.get(elem_a) == elem_b:
            return {"relation": "相生", "score": 90}
        if cycle.get(elem_b) == elem_a:
            return {"relation": "受生", "score": 80}
        return {"relation": "相克", "score": 30}

    def family_environment_analysis(self, person):
        """Analyze how family environment affected a person's destiny"""
        bazi_result = getattr(person, "_bazi_cache", None) or self.bazi.calculate(
            getattr(person, "birth_year", 0),
            getattr(person, "birth_month", 1),
            getattr(person, "birth_day", 1),
            getattr(person, "birth_hour", 12),
        )
        if not hasattr(person, "_bazi_cache"):
            person._bazi_cache = bazi_result

        family_rank = getattr(person, "family_rank", 0)
        family_wealth = getattr(person, "family_wealth", "")
        birth_order = getattr(person, "birth_order", 1)
        element = bazi_result.get("day_master_element", "土")
        dominant = bazi_result.get("elements", {}).get("dominant", "土")

        social_mobility = "高"
        if family_rank <= 2 and dominant in ["火", "金"]:
            social_mobility = "极高 - 寒门贵子"
        elif family_rank >= 4 and dominant in ["土", "水"]:
            social_mobility = "维持 - 世家传承"

        sibling_effect = "强"
        if birth_order <= 2:
            sibling_effect = "长子效应 - 责任型"
        elif birth_order >= 4:
            sibling_effect = "幼子效应 - 自由型"

        wealth_hint = "高" if family_wealth in ["富裕", "极高"] else "中" if family_wealth else "低"

        return {
            "social_mobility": social_mobility,
            "sibling_effect": sibling_effect,
            "family_wealth_hint": wealth_hint,
            "element_vs_family": f"{element}行生于{['贫寒','普通','富裕','显赫'][min(family_rank,3)]}之家",
            "recommendation": "宜借贵人提携" if family_rank <= 2 else "宜守成发展",
        }
