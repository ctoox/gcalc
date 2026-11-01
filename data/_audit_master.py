"""Full quality check of master_10k. 10164 people."""
import json
from collections import Counter

path = r'C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data\master_10k.json'
with open(path, encoding='utf-8') as f:
    data = json.load(f)
ps = data.get("persons", [])

print(f"Total: {len(ps)}")
print()

# 1. Year range
years = [p.get("birth_year", 0) for p in ps]
print(f"Birth year: min={min(years)} max={max(years)}")
ancient = sum(1 for y in years if y < 0)
modern = sum(1 for y in years if 1800 <= y <= 2026)
print(f"  Ancient (BC): {ancient}, Modern (1800+): {modern}, Unknown (0): {years.count(0)}")

# 2. Month/day quality
bad_month = sum(1 for p in ps if p.get("birth_month", 0) not in range(1,13))
bad_day = sum(1 for p in ps if p.get("birth_day", 0) not in range(1,32))
print(f"Bad month: {bad_month}, Bad day: {bad_day}")

# 3. Death quality
no_death = sum(1 for p in ps if not p.get("death_year"))
death_before_birth = sum(1 for p in ps if p.get("death_year") and p.get("birth_year") and p["death_year"] < p["birth_year"])
print(f"No death: {no_death}, Death<birth: {death_before_birth}")

# 4. Lifespan outliers
lifespans = [p["death_year"] - p["birth_year"] for p in ps if p.get("death_year") and p.get("birth_year") and p["death_year"] > p["birth_year"]]
too_old = sum(1 for l in lifespans if l > 120)
too_young = sum(1 for l in lifespans if l < 0)
print(f"Lifespan: {min(lifespans)}-{max(lifespans)}, avg={sum(lifespans)/len(lifespans):.0f}")
print(f"  Over 120: {too_old}, Negative: {too_young}")

# 5. Gender balance
genders = Counter(p.get("gender") for p in ps)
print(f"Gender: {dict(genders)}")

# 6. Nationality top
nats = Counter(p.get("nationality", "") for p in ps)
print(f"Nationalities: {len(nats)}, top: {nats.most_common(10)}")

# 7. Occupation top
occs = Counter(p.get("occupation", "") for p in ps)
print(f"Occupations: {len(occs)}, top: {occs.most_common(10)}")

# 8. Source distribution
sources = Counter(p.get("source", "") for p in ps)
print(f"Sources: {dict(sources)}")

# 9. Twin group analysis
twin_ids = Counter(p.get("twin_group_id") for p in ps if p.get("twin_group_id"))
print(f"Twin groups: {len(twin_ids)}")
print(f"  Twin group sizes: {Counter(twin_ids.values()).most_common(5)}")

# 10. BaZi quality
bazi_empty = sum(1 for p in ps if not p.get("bazi"))
print(f"Missing BaZi: {bazi_empty}")

# 11. Sample ancient people (check if BaZi valid for BC dates)
print("\n=== Ancient people sample ===")
for p in ps:
    if p.get("birth_year", 0) < 0:
        print(f"  {p['name']}: {p['birth_year']}年 {p.get('bazi','')} {p.get('occupation','')}")
        if sum(1 for _ in range(5)) > 5: break

# 12. Find duplicates by (name, birth_year)
print("\n=== Near-duplicate check ===")
from collections import defaultdict
by_key = defaultdict(list)
for p in ps:
    n = p.get("name", "")
    y = p.get("birth_year", 0)
    by_key[(n, y)].append(p)
multi = {k: v for k, v in by_key.items() if len(v) > 1}
print(f"Duplicate (name+birth_year): {len(multi)}")
for k, v in list(multi.items())[:5]:
    print(f"  {k}: {len(v)} entries")

print("\n=== Missing/critical fields check ===")
essential = ["name", "birth_year", "birth_month", "birth_day", "death_year", "bazi"]
for f in essential:
    missing = sum(1 for p in ps if not p.get(f))
    print(f"  {f}: {missing} missing")

# 13. Category distribution
cats = Counter(p.get("category", "") for p in ps)
print(f"\nCategories: {cats.most_common(10)}")

# 14. Environment tags
env_tags = Counter()
for p in ps:
    for t in p.get("environment_tags", []):
        env_tags[t] += 1
print(f"Environment tags: {env_tags.most_common(10)}")
