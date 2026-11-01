"""Verify SQLite database after migration"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.db import get_db

db = get_db()
s = db.stats()
print(f"DB size: {s['db_size_mb']}MB")
print(f"Total people: {s['total']}")
print(f"Verified: {s['verified']}")
print(f"Has BaZi: {s['has_bazi']}")
print(f"Has death: {s['has_death']}")
print(f"Nationalities: {s['nationalities']}")
print(f"Occupations: {s['occupations']}")
print(f"Twin groups: {s['twin_groups']}")
print(f"Genders: {s['genders']}")
print(f"By century: {[(r['century'], r['cnt']) for r in s['by_century']]}")
print(f"Top nationalities: {[(r['nationality'], r['cnt']) for r in s['top_nationalities'][:5]]}")
print(f"Top occupations: {[(r['occupation'], r['cnt']) for r in s['top_occupations'][:5]]}")
print(f"Last migration: {s['last_migration']}")

# Sample
print("\n=== Random sample ===")
for p in db.random(5):
    print(f"  {p['name']}: {p['birth_year']}-{p['birth_month']:02d}-{p['birth_day']:02d} h={p['birth_hour']} death={p['death_year']} {p['nationality']} {p['occupation']} bazi={p['bazi']}")

# Search test
print("\n=== FTS search: 'Einstein' ===")
results, total = db.search("Einstein")
print(f"Found {total}:")
for p in results[:3]:
    print(f"  {p['name']}: {p['birth_year']} {p['occupation']}")

# Filter test
print("\n=== Filter: scientists ===")
results, total = db.filter(category="scientist", per_page=5)
print(f"Total scientists: {total}")
for p in results[:3]:
    print(f"  {p['name']}: {p['birth_year']} {p['occupation']}")

# Get by rowid
print("\n=== Einstein by rowid ===")
p = db.get_by_name("Albert Einstein_1879")
if not p:
    p = db.search("Einstein")
    if p[0]:
        p = p[0][0]
print(f"  {p['name']}: {p['bazi']} conf={p['confidence']} src={p['source']}")

# DB file check
db_path = db.db_path
size_mb = os.path.getsize(db_path) / 1024 / 1024
print(f"\nDB file: {db_path} ({size_mb:.1f}MB)")
print(f"JSON equivalent (master_10k): 59MB -> SQLite: {size_mb:.1f}MB = {size_mb/59*100:.0f}% of original")
