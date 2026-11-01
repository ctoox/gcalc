"""Test CJK search fix"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.db import get_db

db = get_db()

tests = [
    ("展程", 1, "罗展程"),
    ("Einstein", 1, "Albert Einstein"),
    ("罗", 1, "罗展程"),
    ("毛泽东", 1, "Mao Zedong"),
    ("科学家", 50, None),  # should find many scientists
    ("Chinese", 50, None),
]

for q, expected_min, expected_name in tests:
    r, t = db.search(q, limit=5)
    status = "PASS" if t >= expected_min else "FAIL"
    print(f"Search '{q}': {t} results (min {expected_min}) {status}")
    if r and expected_name:
        found = any(expected_name in p['name'] for p in r)
        print(f"  found '{expected_name}': {'PASS' if found else 'FAIL'}")

print("\nAll CJK search tests done.")
