"""Quick test: start Flask and hit API endpoints"""
import subprocess, time, requests, sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.db import get_db

# Test database directly first
db = get_db()
s = db.stats()
print(f"DB: {s['total']} people")
assert s['total'] == 10164, f"Expected 10164, got {s['total']}"
assert s['has_bazi'] == 10164
print("DB direct test: PASS")

# Test search
r, t = db.search("Einstein")
assert t == 1 and r[0]['name'] == 'Albert Einstein'
print(f"FTS search 'Einstein': {t} result(s) - PASS")

# Test filter
r, t = db.filter(category="scientist", per_page=5)
assert t == 3490
print(f"Filter scientists: {t} - PASS")

# Test random
r = db.random(3)
assert len(r) == 3
print(f"Random: {[p['name'] for p in r]} - PASS")

# Test stats
assert isinstance(s['top_nationalities'], list)
assert isinstance(s['top_occupations'], list)
print("Stats: PASS")

print("\nAll database tests PASSED!")
print(f"\nDB file: {db.db_path} ({db._db_size_mb()}MB)")
