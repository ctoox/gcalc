"""Fortune reading for 罗展程, 1997-06-21 - output to file to avoid terminal encoding issues"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.fusion_v2 import FusionV2
from core.bazi import BaziEngine
from core.western import WesternEngine
from core.yearly import YearlyEngine
from core.qimen import QiMenEngine
from core.family_deep import FamilyDeepAnalyzer
from datetime import date

name = "罗展程"
year, month, day, hour = 1997, 6, 21, 12
gender = "男"

be = BaziEngine()
we = WesternEngine()
ye = YearlyEngine()
qme = QiMenEngine()
fda = FamilyDeepAnalyzer()

bazi = be.calculate(year, month, day, hour)
western = we.calculate_chart(date(year, month, day), hour)

# Fusion
engine = FusionV2()
result = engine.analyze(year, month, day, hour, name, gender, rank=2)
fs = result["fusion"]

# Family
family_deep = fda.analyze(bazi, {})

# Monthly current year
current_year = 2026
yearly = result.get("yearly", {})
cy = yearly.get(str(current_year), {})

# Qimen today
now = date.today()
qm = qme.calculate(now.year, now.month, now.day, hour)

output = {
    "姓名": name,
    "出生": f"{year}年{month}月{day}日 {hour}时",
    "八字": {
        "四柱": bazi.get("bazi", ""),
        "日主": bazi.get("day_master_element", ""),
        "五行": {
            "旺": bazi.get("elements", {}).get("dominant", ""),
            "缺": bazi.get("elements", {}).get("missing", []),
        },
        "藏干": bazi.get("hidden_stems", []),
        "性格": bazi.get("personality", ""),
        "事业倾向": bazi.get("career_affinity", []),
    },
    "财富": bazi.get("wealth_potential", {}),
    "大运": bazi.get("major_fortune", []),
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
        "冲克": cy.get("conflict", []),
        "风险分": cy.get("accident_risk", 0),
        "事件倾向": cy.get("event_tendencies", []),
    },
    "奇门今日": {
        "门": qm.get("door", ""),
        "星": qm.get("star", ""),
        "神": qm.get("spirit", ""),
        "风险": qm.get("risk_score", 0),
    },
    "深度家庭": {
        "童年分": family_deep.get("childhood_score", 0),
        "家庭财富": family_deep.get("family_wealth", ""),
        "社会流动": family_deep.get("social_mobility", ""),
        "隐藏信息": family_deep.get("hidden_secrets", []),
    },
    "统计样本": {
        "案例": result["statistical_evidence"].get("total_cases", 0),
        "命局模式": result["statistical_evidence"].get("total_patterns", 0),
    },
}

# Write to file
out_path = os.path.join(os.path.dirname(__file__), "luozhancheng_report.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Also print a summary that avoids Chinese chars
score = fs['score']
print(f"==={name}===")
print(f"Score: {score}/100 (v{fs['calibration_version']}, +/-{fs['confidence_interval']:.0f})")
print(f"BaZi: {bazi.get('bazi', '')}")
print(f"Day Master: {bazi.get('day_master_element', '')}")
print(f"Missing: {bazi.get('elements', {}).get('missing', [])}")
print(f"Dominant: {bazi.get('elements', {}).get('dominant', '')}")
print(f"Personality: {bazi.get('personality', '')}")
print(f"Career affinity: {bazi.get('career_affinity', [])}")
print(f"Wealth: level={bazi.get('wealth_potential', {}).get('level', '')} score={bazi.get('wealth_potential', {}).get('score', 0)}")
print(f"Sun: {western.get('sun_sign', '')} Moon: {western.get('moon_sign', '')} Rising: {western.get('rising_sign', '')}")
print(f"Element balance: {western.get('element_balance', {})}")
print(f"East: {fs['east_score']:.1f} West: {fs['west_score']:.1f} Num: {fs['num_score']:.1f}")
print(f"Career overlap: {result['career'].get('overlap', [])[:5]}")
print(f"Lifespan: {result['lifespan'].get('estimate', '?')}")
print(f"2026: {cy.get('year_gz', '')} risk={cy.get('accident_risk',0)}")
print(f"Qimen today: door={qm.get('door','')} risk={qm.get('risk_score',0)}")
print(f"Family childhood: {family_deep.get('childhood_score',0)}/100 mobility={family_deep.get('social_mobility','')}")
print(f"Stats: {result['statistical_evidence'].get('total_cases',0)} cases")
print(f"Accuracy: {fs['accuracy']:.1f}%")
print(f"Full report written to luozhancheng_report.json")
