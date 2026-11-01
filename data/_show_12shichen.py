"""Read 12 shichen results for 罗展程 from the previously computed data"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.shichen_analyzer import ShiChenAnalyzer

a = ShiChenAnalyzer()
results = a.analyze_all(1997, 6, 21, "罗展程", "男")

# Write JSON
out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "luozhancheng_12shichen.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Print ranking
print(f"=== 12时辰 ranking for 罗展程 (1997-06-21) ===")
print(f"{'Rank':>4} {'时辰':>4} {'Hour':>4} {'八字':>22} {'日主':>4} {'缺':>4} {'East':>5} {'West':>5} {'Score':>6}")
print("=" * 75)
for i, r in enumerate(results):
    miss = "/".join(r["missing"]) if r.get("missing") else "-"
    print(f"{i+1:>4} {r['时辰']:>4} {r['hour']:>4} {r['bazi']:>22} {r['day_master']:>4} {miss:>4} {r['east']:>5.0f} {r['west']:>5.0f} {r['total_score']:>6.1f}")

print(f"\nFile saved: {out_path}")
