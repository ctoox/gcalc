"""Calibrated life report for 罗展程 with real events mapped"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.life_report import LifeReport

# Real life events for calibration
real_events = [
    {"year": 2015, "age": 19, "event": "当兵入伍", "type": "career_change", "confirmed": True},
    {"year": 2017, "age": 21, "event": "当兵结束, 二叔外公去世", "type": "family_loss", "confirmed": True},
    {"year": 2018, "age": 22, "event": "上大专", "type": "education", "confirmed": True},
    {"year": 2020, "age": 24, "event": "运维工程师(中长康达外包驻场怡园小学)", "type": "career", "confirmed": True},
    {"year": 2022, "age": 26, "event": "运维工程师(天河智慧城南方基地)", "type": "career_change", "confirmed": True},
    {"year": 2023, "age": 27, "event": "AI盛行炒币有亏有赚", "type": "investment", "confirmed": True},
    {"year": 2025, "age": 29, "event": "开始送外卖", "type": "career_change", "confirmed": True},
    {"year": 2026, "age": 30, "event": "送外卖日赚不到100,家里负债", "type": "financial_stress", "confirmed": True},
]

# Family background correction
family_correction = {
    "father_side": "入赘,好赌,负债",
    "family_wealth_actual": "负债",
    "social_mobility_actual": "低",
    "childhood_score_actual": 35,
}

lr = LifeReport()
report = lr.generate(
    year=1997, month=6, day=22,
    hour=1,  # 丑时
    name="罗展程",
    gender="男",
    calibration_data=real_events,
)

# Override family with real data
report["family"]["actual_family_wealth"] = family_correction["family_wealth_actual"]
report["family"]["actual_social_mobility"] = family_correction["social_mobility_actual"]
report["family"]["actual_childhood_score"] = family_correction["childhood_score_actual"]
report["family"]["father_side_note"] = family_correction["father_side"]
report["family_calibrated"] = True

# Annotate timeline with user's real events for comparison
for ty in report["yearly_timeline"]:
    matching_re = [e for e in real_events if e["year"] == ty["year"]]
    if matching_re:
        ty["real_event"] = matching_re[0]["event"]
        # Compare prediction vs reality
        pred_types = [ev.get("type") for ev in ty.get("events", [])]
        re_type = matching_re[0].get("type", "")
        if re_type == "family_loss" and ("丧门" in str(ty.get("spirits_bad", [])) or "丧" in str(ty.get("events", []))):
            ty["calibration"] = "MATCH"
        elif re_type == "career_change" and ("驿马" in str(ty.get("spirits_good", [])) or "日犯岁君" in str(ty.get("conflicts", []))):
            ty["calibration"] = "MATCH"
        elif re_type == "financial_stress" and ("大耗" in str(ty.get("spirits_bad", [])) or "劫煞" in str(ty.get("spirits_bad", []))):
            ty["calibration"] = "MATCH"
        else:
            ty["calibration"] = "PARTIAL"
    else:
        ty["real_event"] = ""
        ty["calibration"] = ""

# Calibration accuracy
matched = sum(1 for ty in report["yearly_timeline"] if ty.get("calibration") == "MATCH")
total_events = sum(1 for ty in report["yearly_timeline"] if ty.get("real_event"))
report["calibration_accuracy"] = round(matched / max(total_events, 1) * 100, 1)

# Add details
report["calibration_events_used"] = real_events

# Save
out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "luozhancheng_calibrated.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

# Print text report with calibration
text = lr.to_text(report)
lines = text.split("\n")

print(f"校准完成: {report['calibration_accuracy']}% 匹配率")
print(f"\n=== 你的真实事件 vs 命盘预测 ===")
print(f"{'年份':>4} {'年龄':>4} {'预测事件':<40} {'校准':>8}")
print("=" * 60)
for ty in report["yearly_timeline"]:
    if not ty.get("real_event"):
        continue
    ev_text = "; ".join(e["text"] for e in ty.get("events", [])[:2]) if ty.get("events") else "-"
    print(f"{ty['year']:>4} {ty['age']:>4} {ev_text:<40} {ty.get('calibration',''):>8}")
    print(f"{'':>10} 实际: {ty['real_event']}")

print(f"\n=== 关键未来预测 ===")
for ty in report["yearly_timeline"]:
    if not ty.get("is_future") or ty["year"] > 2032:
        continue
    evs = "; ".join(e["text"] for e in ty.get("events", [])[:3])
    s = ty.get("scores", {})
    print(f"  {ty['year']}年({ty['age']}岁) {ty['gan_zhi']} 事{s.get('career',0)} 财{s.get('wealth',0)} 爱{s.get('love',0)}")
    if evs:
        print(f"    → {evs}")

print(f"\n报告已保存: {out_path}")
print(f"校准匹配率: {report['calibration_accuracy']}%")
