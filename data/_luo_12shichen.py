"""Run 12 时辰 analysis for 罗展程"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.shichen_analyzer import ShiChenAnalyzer

a = ShiChenAnalyzer()
results = a.analyze_all(1997, 6, 21, "罗展程", "男")

out = []
print(f"12 时辰分析 for 罗展程 (1997-06-21):")
print(f"{'时辰':>6} | {'八字':>22} | {'日主':>4} | {'缺':>6} | {'东':>5} | {'西':>5} | {'评分':>6} | {'总分':>6} | {'事业':>20}")
print("=" * 90)
for r in results:
    miss = "/".join(r["missing"]) if r["missing"] else "无"
    career = ",".join(r["career"])[:20] if r.get("career") else ""
    out.append(r)
    print(f"{r['时辰']:>6} | {r['bazi']:>22} | {r['day_master']:>4} | {miss:>6} | {r['east']:>4.0f} | {r['west']:>4.0f} | {r['score']:>5.1f} | {r['total_score']:>5.1f} | {career:>20}")

print(f"\nBest match: {results[0]['时辰']} (total={results[0]['total_score']})")
print(f"User hour: 午时 (12:00) → rank {next(i+1 for i,r in enumerate(results) if r['hour']==12)}")

# Write full data
with open(os.path.join(os.path.dirname(__file__), "luozhancheng_12shichen.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\nFull report saved to luozhancheng_12shichen.json")
