"""Generate comprehensive life report for 罗展程"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.life_report import LifeReport

lr = LifeReport()
report = lr.generate(
    year=1997, month=6, day=22,
    hour=1,  # 丑时 (best match from 12时辰 analysis)
    name="罗展程",
    gender="男",
)

# Save JSON
out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "luozhancheng_life_report.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"JSON saved to {out_path}")

# Print text
text = lr.to_text(report)
print(text)

# Also save text
txt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "luozhancheng_life_report.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(text)
print(f"\nText saved to {txt_path}")
