"""Corrected reading for 罗展程 - Gregorian 1997-06-22 (Lunar 1997-05-18)"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.fusion_v2 import FusionV2
from core.bazi import BaziEngine
from core.western import WesternEngine
from core.yearly import YearlyEngine
from core.qimen import QiMenEngine
from core.family_deep import FamilyDeepAnalyzer
from core.shichen_analyzer import ShiChenAnalyzer
from datetime import date

name = "罗展程"
year, month, day = 1997, 6, 22  # Corrected: Gregorian from Lunar 1997-05-18
gender = "男"

print(f"Corrected date: {year}-{month:02d}-{day:02d}")
print("=" * 60)

# ── 12时辰 analysis ──
sa = ShiChenAnalyzer()
sc_results = sa.analyze_all(year, month, day, name, gender)

print("\n12时辰 ranking:")
print(f"{'Rank':>4} {'时辰':>6} {'八字':>22} {'日主':>4} {'旺':>4} {'东':>5} {'西':>5} {'评分':>6} {'总分':>6}")
print("-" * 75)
for i, r in enumerate(sc_results):
    miss = "/".join(r["missing"]) if r.get("missing") else "全"
    print(f"{i+1:>4} {r['时辰']:>6} {r['bazi']:>22} {r['day_master']:>4} {r['dominant']:>4} {r['east']:>5.0f} {r['west']:>5.0f} {r['score']:>5.1f} {r['total_score']:>6.1f}")

best = sc_results[0]
best_hour = best['hour']
print(f"\nBest match: {best['时辰']} (hour={best_hour})")

# ── Full analysis with best hour ──
be = BaziEngine()
we = WesternEngine()
ye = YearlyEngine()
qme = QiMenEngine()
fda = FamilyDeepAnalyzer()

bazi = be.calculate(year, month, day, best_hour)
western = we.calculate_chart(date(year, month, day), best_hour)
engine = FusionV2()
result = engine.analyze(year, month, day, best_hour, name, gender, rank=2)
fs = result["fusion"]
family_deep = fda.analyze(bazi, {})
now = date.today()
qm = qme.calculate(now.year, now.month, now.day, best_hour)

# Current year
current_year = 2026
yearly = result.get("yearly", {})
cy = yearly.get(str(current_year), {})

output = {
    "姓名": name,
    "出生": f"{year}年{month}月{day}日 (农历丁丑年五月十八)",
    "最佳时辰": best["时辰"],
    "八字": {
        "四柱": bazi.get("bazi", ""),
        "日主": bazi.get("day_master_element", ""),
        "五行旺": bazi.get("elements", {}).get("dominant", ""),
        "五行缺": bazi.get("elements", {}).get("missing", []),
        "藏干": bazi.get("hidden_stems", []),
        "性格": bazi.get("personality", ""),
        "事业倾向": bazi.get("career_affinity", []),
    },
    "财富": bazi.get("wealth_potential", {}),
    "占星": {
        "太阳": western.get("sun_sign", ""),
        "月亮": western.get("moon_sign", ""),
        "上升": western.get("rising_sign", ""),
        "元素平衡": western.get("element_balance", {}),
    },
    "融合评分": {
        "综合": f'{fs["score"]}/100',
        "校准版": fs["calibration_version"],
        "置信区间": f'±{fs["confidence_interval"]:.0f}',
        "东方": round(fs["east_score"], 1),
        "西方": round(fs["west_score"], 1),
        "数理": round(fs["num_score"], 1),
        "统计": round(fs.get("stat_score", 0), 1),
        "系统精度": f'{fs["accuracy"]:.1f}%',
    },
    "事业": {
        "交集": result["career"].get("overlap", [])[:5],
        "八字倾向": result["career"].get("east_affinity", [])[:5],
        "占星倾向": result["career"].get("west_affinity", [])[:5],
    },
    "寿命参考": result["lifespan"].get("estimate", ""),
    f"{current_year}年流年": {
        "干支": cy.get("year_gz", ""),
        "神煞": cy.get("shensha", []),
        "风险分": cy.get("accident_risk", 0),
    },
    "奇门今日": {
        "门": qm.get("door", {}).get("name", ""),
        "星": qm.get("star", {}).get("name", ""),
        "神": qm.get("spirit", {}).get("name", ""),
        "风险": qm.get("risk_score", 0),
    },
    "深度家庭": {
        "童年分": family_deep.get("childhood_score", 0),
        "家庭财富": family_deep.get("family_wealth", ""),
        "社会流动": family_deep.get("social_mobility", ""),
    },
}

out_path = os.path.join(os.path.dirname(__file__), "luozhancheng_corrected.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nFull report saved to luozhancheng_corrected.json")
print(f"\nCorrected date BaZi: {bazi.get('bazi', '')} (day master: {bazi.get('day_master_element', '')})")
print(f"Previous (June 21): 丁丑 己亥 庚辰 戊午 (日主金)")
print(f"Corrected (June 22): {bazi.get('bazi', '')} (日主{bazi.get('day_master_element', '')})")
