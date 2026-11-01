"""Test: same birth data + different name → different results"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.fusion_v2 import FusionV2

engine = FusionV2()

# Same birth data, different names
test_cases = [
    ("罗展程", 1997, 6, 22, 1, "男"),
    ("罗展程 ", 1997, 6, 22, 1, "男"),  # trailing space → same as above
    ("毛泽东", 1997, 6, 22, 1, "男"),   # different name
    ("张三", 1997, 6, 22, 1, "男"),     # different name
    ("爱因斯坦", 1997, 6, 22, 1, "男"), # different name
    ("罗展程", 1993, 12, 26, 1, "男"), # same name, different date
]

print(f"{'Name':>16} {'Date':>12} {'Score':>6} {'East':>5} {'West':>5} {'NameScore':>9} {'NameEl':>12} {'Sig':>16}")
print("=" * 85)

scores = set()
for name, y, m, d, h, g in test_cases:
    r = engine.analyze(y, m, d, h, name.strip(), g)
    fs = r["fusion"]
    score = fs["score"]
    scores.add(score)
    print(f"{name:>16} {y}-{m:02d}-{d:02d} {fs['score']:>6.1f} {fs['east_score']:>5.0f} {fs['west_score']:>5.0f} {fs.get('name_score',0):>8.0f} {fs.get('name_element_influence',''):>12} {r.get('signature',''):>16}")

print(f"\nUnique scores: {len(scores)}/{len(test_cases)}")
print(f"All unique: {'PASS' if len(scores) == len(test_cases) else 'FAIL - duplicates found!'}")
