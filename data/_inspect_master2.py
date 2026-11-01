"""Deep inspect master_10k persons array"""
import json

path = r'C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data\master_10k.json'
with open(path, encoding='utf-8') as f:
    data = json.load(f)

persons = data.get("persons", [])
print(f"Persons count: {len(persons)}")

# Show summary
summary = data.get("summary", {})
print(f"Summary: {summary}")

# Sample people
print("\n--- First 10 people ---")
for i, p in enumerate(persons[:10]):
    name = p.get("name", "?")
    by = p.get("birth_year", "?")
    bm = p.get("birth_month", "?")
    bd = p.get("birth_day", "?")
    bh = p.get("birth_hour", "?")
    dy = p.get("death_year", "?")
    occ = p.get("occupation", p.get("career", "?"))
    bazi = p.get("bazi", "")
    conf = p.get("confidence", "?")
    src = p.get("source", "?")
    qual = p.get("quality_tags", [])
    print(f"  [{i}] {name}: {by}-{bm:02d}-{bd:02d} h={bh} death={dy} occ={occ} bazi={bazi} conf={conf} src={src} tags={qual}")

# Field frequency
print("\n--- All field names ---")
field_counts = {}
for p in persons:
    for k in p:
        field_counts[k] = field_counts.get(k, 0) + 1
for k, v in sorted(field_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}/{len(persons)}")

# Data quality
has_real_name = sum(1 for p in persons if p.get("name"))
has_bazi = sum(1 for p in persons if p.get("bazi"))
has_birth = sum(1 for p in persons if p.get("birth_year"))
has_death = sum(1 for p in persons if p.get("death_year") or p.get("death_cause"))
has_confidence = sum(1 for p in persons if p.get("confidence"))
chinese = sum(1 for p in persons if p.get("source_priority") == 10)
print(f"\n--- Quality ---")
print(f"  Total: {len(persons)}")
print(f"  Has name: {has_real_name}")
print(f"  Has birth year: {has_birth}")
print(f"  Has BaZi: {has_bazi}")
print(f"  Has death: {has_death}")
print(f"  Has confidence: {has_confidence}")
print(f"  Chinese (priority 10): {chinese}")

# Duplicate names
from collections import Counter
names = [p.get("name", "") for p in persons if p.get("name")]
name_counts = Counter(n for n in names if n)
dups = {k: v for k, v in name_counts.items() if v > 1}
print(f"\n  Duplicate names: {len(dups)} groups")
for n, c in list(dups.items())[:10]:
    years = [p.get("birth_year") for p in persons if p.get("name") == n]
    print(f"    {n}: {c}次 (births: {years})")
