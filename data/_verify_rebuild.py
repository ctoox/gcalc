"""Verify rebuilt real_people.json"""
import json, os

path = r'C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data\real_people.json'
size = os.path.getsize(path)
print(f"File size: {size:,} bytes ({size/1024/1024:.1f} MB)")

with open(path, encoding='utf-8') as f:
    data = json.load(f)

print(f"Entries: {len(data)}")
print(f"Type: dict")

# Sample
items = list(data.items())
print(f"\n=== First 5 ===")
for k, v in items[:5]:
    print(f"  [{k}] name={v.get('name','?')} year={v.get('birth_year')} bazi={v.get('bazi','')} conf={v.get('confidence')}")

# Verify no empty names
empty = sum(1 for k, v in items if not v.get("name"))
print(f"\nEmpty names: {empty}")
nobody = sum(1 for k, v in items if v.get("name") == "?")
print(f"  '?' names: {nobody}")

# All have bazi?
no_bazi = sum(1 for k, v in items if not v.get("bazi"))
print(f"Missing BaZi: {no_bazi}")

# Check max bazi length
bazi_lengths = [len(v.get("bazi", "")) for k, v in items]
print(f"BaZi lengths: min={min(bazi_lengths)} max={max(bazi_lengths)}")

# Chinese people
chinese = [(k, v) for k, v in items if v.get("nationality") in ["Chinese", "Chinese American", ""] and v.get("source_priority") == 10]
print(f"\nChinese (source_priority=10): {len(chinese)}")
for k, v in chinese[:10]:
    print(f"  {v.get('name','?')}: {v.get('birth_year')} {v.get('nationality')}")

# Death cause
has_death_cause = sum(1 for k, v in items if v.get("death_cause"))
print(f"\nHas death_cause: {has_death_cause}")

# Occupation diversity
occs = set()
for k, v in items:
    o = v.get("occupation", "")
    if o:
        occs.add(o)
print(f"Unique occupations: {len(occs)}")

# Nationalities
nats = set()
for k, v in items:
    n = v.get("nationality", "")
    if n:
        nats.add(n)
print(f"Unique nationalities: {len(nats)}")

print("\nAll checks: PASS" if (empty == 0 and no_bazi == 0) else "\nFAILURES DETECTED!")
