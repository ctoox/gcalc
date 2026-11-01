"""Death pattern analyzer.
Analyzes known death cases (US presidents, accidental deaths) to find
common BaZi patterns, 流年 triggers, and Qi Men signatures.
Reverse-engineers accident causes from well-documented deaths."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi import BaziEngine
from core.western import WesternEngine
from core.yearly import YearlyEngine, year_gan_zhi, LIU_CHONG, WU_XING_GAN
from core.qimen import QiMenEngine
from datetime import date

# Enhanced assassination patterns
QI_SHA = {"甲":"庚","乙":"辛","丙":"壬","丁":"癸","戊":"甲","己":"乙","庚":"丙","辛":"丁","壬":"戊","癸":"己"}
YANG_REN = {"甲":"卯","丙":"午","戊":"午","庚":"酉","壬":"子"}

# US Presidents with known death details
PRESIDENTS = [
    {"name": "George Washington", "b": (1732,2,22,10), "d": (1799,12,14,22), "cause": "急性喉炎/放血治疗"},
    {"name": "John Adams", "b": (1735,10,30,8), "d": (1826,7,4,18), "cause": "自然衰老(90岁)"},
    {"name": "Thomas Jefferson", "b": (1743,4,13,9), "d": (1826,7,4,12), "cause": "自然衰老(83岁)"},
    {"name": "William H. Harrison", "b": (1773,2,9,6), "d": (1841,4,4,0), "cause": "肺炎(就职1月后死亡)"},
    {"name": "Abraham Lincoln", "b": (1809,2,12,7), "d": (1865,4,15,7), "cause": "暗杀/头部中枪"},
    {"name": "James Garfield", "b": (1831,11,19,10), "d": (1881,9,19,22), "cause": "暗杀/枪伤感染"},
    {"name": "William McKinley", "b": (1843,1,29,8), "d": (1901,9,14,3), "cause": "暗杀/腹部中枪坏疽"},
    {"name": "Theodore Roosevelt", "b": (1858,10,27,8), "d": (1919,1,6,4), "cause": "冠状动脉血栓"},
    {"name": "Warren G. Harding", "b": (1865,11,2,11), "d": (1923,8,2,19), "cause": "心脏病/可能中毒"},
    {"name": "Franklin D. Roosevelt", "b": (1882,1,30,8), "d": (1945,4,12,15), "cause": "脑溢血"},
    {"name": "John F. Kennedy", "b": (1917,5,29,14), "d": (1963,11,22,12), "cause": "暗杀/头部中枪"},
    {"name": "Richard Nixon", "b": (1913,1,9,21), "d": (1994,4,22,21), "cause": "中风"},
    {"name": "Ronald Reagan", "b": (1911,2,6,4), "d": (2004,6,5,13), "cause": "阿尔茨海默症(曾遇刺幸存)"},
]

# Chinese celebrities with known deaths
CHINESE_DEATHS = [
    {"name": "鲁迅", "b": (1881,9,25,12), "d": (1936,10,19,5), "cause": "肺结核"},
    {"name": "孙中山", "b": (1866,11,12,11), "d": (1925,3,12,9), "cause": "肝癌"},
    {"name": "周恩来", "b": (1898,3,5,8), "d": (1976,1,8,9), "cause": "膀胱癌"},
    {"name": "毛泽东", "b": (1893,12,26,10), "d": (1976,9,9,0), "cause": "渐进性衰老/ALS"},
    {"name": "诸葛亮", "b": (181,4,14,12), "d": (234,10,3,8), "cause": "积劳成疾"},
    {"name": "岳飞", "b": (1103,3,24,10), "d": (1142,1,28,12), "cause": "冤杀"},
]

# Accidental deaths (non-political)
ACCIDENTAL_DEATHS = [
    {"name": "李小龙", "b": (1940,11,27,7), "d": (1973,7,20,23), "cause": "脑水肿/药物反应"},
    {"name": "迈克尔·杰克逊", "b": (1958,8,29,12), "d": (2009,6,25,14), "cause": "药物过量"},
    {"name": "戴安娜王妃", "b": (1961,7,1,19), "d": (1997,8,31,0), "cause": "车祸"},
    {"name": "玛丽莲·梦露", "b": (1926,6,1,9), "d": (1962,8,5,4), "cause": "药物过量/疑谋杀"},
    {"name": "黄家驹", "b": (1962,6,10,14), "d": (1993,6,30,16), "cause": "舞台坠落"},
    {"name": "张国荣", "b": (1956,9,12,13), "d": (2003,4,1,18), "cause": "跳楼自杀"},
    {"name": "邓丽君", "b": (1953,1,29,11), "d": (1995,5,8,17), "cause": "哮喘发作"},
    {"name": "保罗·沃克", "b": (1973,9,12,10), "d": (2013,11,30,15), "cause": "车祸"},
]


class DeathAnalyzer:
    def __init__(self):
        self.bazi = BaziEngine()
        self.western = WesternEngine()
        self.yearly = YearlyEngine()
        self.qimen = QiMenEngine()

    def _assassination_analysis(self, bazi_result, death_year):
        """Special analysis for assassination/unnatural death patterns."""
        patterns = []
        extra_risk = 0

        day_gan = ""
        day_zhi = ""
        bazi_str = bazi_result.get("bazi", "")
        pillars = bazi_str.split() if bazi_str else []
        if len(pillars) > 2:
            day_pillar = pillars[2]
            day_gan = day_pillar[0] if len(day_pillar) > 0 else ""
            day_zhi = day_pillar[1] if len(day_pillar) > 1 else ""

        yg, yz = year_gan_zhi(death_year)

        # 七杀攻身: 流年天干为日主的七杀
        if day_gan in QI_SHA and yg == QI_SHA[day_gan]:
            patterns.append(f"流年天干{yg}为日主{day_gan}之七杀,凶")
            extra_risk += 25

        # 羊刃倒戈: 流年地支为日主的羊刃
        if day_gan in YANG_REN and yz == YANG_REN[day_gan]:
            patterns.append(f"流年{z}为日主{day_gan}之羊刃,血光")
            extra_risk += 30

        # 天克地冲: year conflicts with day pillar
        day_gan_el = WU_XING_GAN.get(day_gan, "")
        yg_el = WU_XING_GAN.get(yg, "")
        ke = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
        if day_zhi and LIU_CHONG.get(yz) == day_zhi and ke.get(yg_el) == day_gan_el:
            patterns.append("天克地冲日柱: 大凶")
            extra_risk += 30

        # 三刑
        if day_zhi and yz:
            xing_groups = [("寅","巳"),("巳","申"),("丑","戌"),("戌","未"),("子","卯")]
            if (day_zhi, yz) in xing_groups or (yz, day_zhi) in xing_groups:
                patterns.append(f"流年{yz}与日支{day_zhi}相刑")
                extra_risk += 15

        return patterns, extra_risk

    def analyze_death(self, name, birth, death, cause=""):
        """Full death analysis for one person."""
        by, bm, bd, bh = birth
        dy, dm, dd, dh = death

        bazi_result = self.bazi.calculate(by, bm, bd, bh)
        western_result = self.western.calculate_chart(date(by, bm, bd), bh)

        # Lifetime timeline
        timeline = self.yearly.analyze_life(bazi_result, by, dy)

        # Death year specific
        death_year_analysis = self.yearly.compare_death_year(timeline, dy)

        # High risk years
        high_risk = self.yearly.find_death_years(timeline)

        # Qi Men analysis of death period
        qimen_death = self.qimen.analyze_death_window(by, dy, cause)

        # Assassination-specific analysis
        assas_pats, assas_extra = self._assassination_analysis(bazi_result, dy)

        # Death year 流年 pattern (boosted by assassination analysis)
        base_risk = death_year_analysis["accident_risk"] if death_year_analysis else 0
        boosted_risk = min(100, base_risk + assas_extra)

        death_pattern = {
            "accident_risk": boosted_risk,
            "conflicts": (death_year_analysis["conflicts"] if death_year_analysis else []) + assas_pats,
            "spirits": death_year_analysis["spirits_bad"] if death_year_analysis else [],
            "events": (death_year_analysis["events"] if death_year_analysis else []) + assas_pats,
        }

        # Was death predicted? (risk level in death year)
        predicted = boosted_risk >= 50

        return {
            "name": name,
            "cause": cause,
            "bazi": bazi_result.get("bazi", ""),
            "day_master": bazi_result.get("day_master_element", ""),
            "day_gan": day_gan if 'day_gan' in dir() else "",
            "missing": bazi_result.get("elements", {}).get("missing", []),
            "dominant": bazi_result.get("elements", {}).get("dominant", ""),
            "death_year": dy,
            "death_age": dy - by,
            "death_year_bazi": death_year_analysis["gan_zhi"] if death_year_analysis else "",
            "death_risk": boosted_risk,
            "predicted": predicted,
            "conflicts": death_pattern["conflicts"],
            "bad_spirits": death_pattern["spirits"],
            "death_events": death_pattern["events"],
            "assassination_patterns": assas_pats,
            "qimen_door": qimen_death["door"]["name"],
            "qimen_star": qimen_death["star"]["name"],
            "qimen_spirit": qimen_death["spirit"]["name"],
            "qimen_risk": qimen_death["risk_score"],
            "overall_risk": (boosted_risk + qimen_death["risk_score"]) / 2,
            "high_risk_years": high_risk[:5],
        }

    def analyze_group(self, group):
        """Analyze a group of deaths and find common patterns."""
        results = []
        for p in group:
            r = self.analyze_death(p["name"], p["b"], p["d"], p["cause"])
            results.append(r)
        return results

    def find_common_patterns(self, results):
        """Find common patterns across all analyzed deaths."""
        common_conflicts = {}
        common_spirits = {}
        common_doors = {}
        common_elements = {}
        predicted_count = 0
        total = len(results)

        for r in results:
            if r["predicted"]:
                predicted_count += 1
            for c in r["conflicts"]:
                common_conflicts[c] = common_conflicts.get(c, 0) + 1
            for s in r["bad_spirits"]:
                common_spirits[s] = common_spirits.get(s, 0) + 1
            d = r["qimen_door"]
            common_doors[d] = common_doors.get(d, 0) + 1
            dm = r["day_master"]
            common_elements[dm] = common_elements.get(dm, 0) + 1

        return {
            "total": total,
            "predicted": predicted_count,
            "prediction_rate": round(predicted_count / max(total, 1) * 100, 1),
            "predicted_count": predicted_count,
            "common_conflicts": sorted(common_conflicts.items(), key=lambda x: -x[1])[:5],
            "common_spirits": sorted(common_spirits.items(), key=lambda x: -x[1])[:5],
            "common_doors": sorted(common_doors.items(), key=lambda x: -x[1])[:5],
            "common_day_masters": sorted(common_elements.items(), key=lambda x: -x[1])[:5],
        }

    def report(self):
        """Generate full death analysis report."""
        sys.stdout.reconfigure(encoding='utf-8')
        print("=" * 60)
        print("          命理死亡模式分析报告")
        print("=" * 60)

        all_groups = {
            "美国总统": PRESIDENTS,
            "中国名人": CHINESE_DEATHS,
            "意外死亡": ACCIDENTAL_DEATHS,
        }

        all_results = []
        for group_name, group in all_groups.items():
            print(f"\n--- {group_name} ---")
            results = self.analyze_group(group)
            all_results.extend(results)
            for r in results:
                risk_str = "⚠️ " if r["predicted"] else "  "
                print(f"  {risk_str}{r['name']}: {r['day_master']}日主 "
                      f"死{r['death_age']}岁 {r['cause']} "
                      f"风险{r['overall_risk']:.0f}/100 "
                      f"八字{r['bazi']} 死年{r['death_year_bazi']}")

        print(f"\n--- 总体模式 ---")
        common = self.find_common_patterns(all_results)
        print(f"  命中率: {common['predicted']}/{common['total']} = {common['prediction_rate']}%")
        print(f"  常见冲突: {common['common_conflicts']}")
        print(f"  常见凶煞: {common['common_spirits']}")
        print(f"  常见八门: {common['common_doors']}")
        print(f"  常见日主: {common['common_day_masters']}")

        return common


if __name__ == "__main__":
    DeathAnalyzer().report()
