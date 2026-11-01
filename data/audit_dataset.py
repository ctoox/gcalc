import json, os
from collections import Counter
from datetime import datetime

DATA_DIR = os.path.dirname(__file__)

def audit(filepath):
    print(f"\n{'='*60}")
    print(f"AUDIT: {os.path.basename(filepath)}")
    print('='*60)

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    persons = raw.get("persons", [])
    events = raw.get("events", [])
    summary = raw.get("summary", {})
    twin_groups = raw.get("twin_groups", {})

    N = len(persons)
    E = len(events)

    print(f"\n1. VOLUME")
    print(f"   Persons:        {N:>8,}")
    print(f"   Events:         {E:>8,}")
    print(f"   Twin groups:    {len(twin_groups):>8,}")
    print(f"   Twin persons:   {summary.get('twin_persons', 0):>8,}")

    print(f"\n2. FIELD COMPLETENESS")
    fields = ["name","birth_year","birth_month","birth_day","birth_hour",
              "death_year","gender","nationality","occupation","bazi",
              "birth_city","birth_country","family_wealth","twin_group_id",
              "environment_tags","verified","source"]
    for f in fields:
        filled = sum(1 for p in persons if p.get(f) is not None and p.get(f) != "" and p.get(f) != 0)
        pct = filled / N * 100 if N else 0
        print(f"   {f:20s}: {filled:>8,} / {N:,} ({pct:5.1f}%)")

    print(f"\n3. GENDER BALANCE")
    gcounter = Counter(p.get("gender", "unknown") for p in persons)
    for g, c in gcounter.most_common():
        print(f"   {g:15s}: {c:>6,} ({c/N*100:5.1f}%)")

    print(f"\n4. BIRTH YEAR DISTRIBUTION")
    years = [p.get("birth_year") for p in persons if p.get("birth_year")]
    if years:
        ymin, ymax = min(years), max(years)
        print(f"   Range: {ymin} - {ymax}")
        bins = [(1500,1599),(1600,1699),(1700,1799),(1800,1899),(1900,1949),(1950,1999),(2000,2026)]
        for lo, hi in bins:
            cnt = sum(1 for y in years if lo <= y <= hi)
            print(f"   {lo}-{hi}: {cnt:>6,} ({cnt/len(years)*100:5.1f}%)")

    print(f"\n5. GEOGRAPHIC COVERAGE")
    nat_counter = Counter(p.get("nationality", "unknown") for p in persons)
    print(f"   Unique nationalities: {len(nat_counter)}")
    for nat, cnt in nat_counter.most_common(15):
        print(f"   {nat:25s}: {cnt:>6,} ({cnt/N*100:5.1f}%)")
    others = N - sum(c for _, c in nat_counter.most_common(15))
    print(f"   {'(remaining)':25s}: {others:>6,} ({others/N*100:5.1f}%)")

    city_counter = Counter(p.get("birth_city", "") for p in persons if p.get("birth_city"))
    print(f"   Unique cities: {len(city_counter)}")

    country_counter = Counter(p.get("birth_country", "") for p in persons if p.get("birth_country"))
    print(f"   Unique countries: {len(country_counter)}")

    print(f"\n6. OCCUPATION COVERAGE")
    occ_counter = Counter(p.get("occupation", "unknown") for p in persons)
    print(f"   Unique occupations: {len(occ_counter)}")
    for occ, cnt in occ_counter.most_common(20):
        print(f"   {occ:25s}: {cnt:>6,} ({cnt/N*100:5.1f}%)")

    print(f"\n7. BAZI / HOUR PRECISION")
    has_hour = sum(1 for p in persons if p.get("birth_hour") is not None)
    has_bazi = sum(1 for p in persons if p.get("bazi"))
    print(f"   With birth_hour:  {has_hour:>8,} ({has_hour/N*100:5.1f}%)")
    print(f"   With bazi:        {has_bazi:>8,} ({has_bazi/N*100:5.1f}%)")
    same_bazi = {}
    for p in persons:
        b = p.get("bazi")
        if b:
            same_bazi.setdefault(b, []).append(p["name"])
    multi = {k:v for k,v in same_bazi.items() if len(v) > 1}
    print(f"   Same-bazi groups: {len(multi)}")
    print(f"   Persons in same-bazi: {sum(len(v) for v in multi.values())}")

    print(f"\n8. EVENT ANALYSIS")
    etypes = Counter(e.get("event_type", "unknown") for e in events)
    print(f"   Unique event types: {len(etypes)}")
    for et, cnt in etypes.most_common(15):
        print(f"   {et:20s}: {cnt:>8,} ({cnt/E*100:5.1f}%)")
    events_per_person = E / N if N else 0
    print(f"   Events per person: {events_per_person:.1f}")
    everified = sum(1 for e in events if e.get("verified"))
    print(f"   Verified events:   {everified:>8,} ({everified/E*100:5.1f}%)")

    print(f"\n9. TWIN DATA QUALITY")
    print(f"   Twin group count: {len(twin_groups)}")
    twin_ids = set()
    for p in persons:
        if p.get("twin_group_id"):
            twin_ids.add(p["twin_group_id"])
    print(f"   Persons with twin_group_id: {sum(1 for p in persons if p.get('twin_group_id'))}")
    twin_with_env = sum(1 for p in persons if p.get("twin_group_id") and p.get("environment_tags"))
    print(f"   Twins with environment_tags: {twin_with_env}")
    twin_with_bazi = sum(1 for p in persons if p.get("twin_group_id") and p.get("bazi"))
    print(f"   Twins with bazi: {twin_with_bazi}")

    print(f"\n10. DATA FRESHNESS")
    exported_at = summary.get("exported_at", "unknown")
    print(f"   Exported: {exported_at}")
    sources = summary.get("sources", {})
    print(f"   Sources: {json.dumps(sources, indent=4)}")

    print(f"\n11. DUPLICATE CHECK")
    names = [p.get("name","") for p in persons]
    dupes = {n for n in names if names.count(n) > 1}
    print(f"   Duplicate names: {len(dupes)}")
    for d in list(dupes)[:10]:
        entries = [p for p in persons if p.get("name") == d]
        print(f"     '{d}' appears {len(entries)} times (sources: {[e.get('source','?') for e in entries]})")

    print(f"\n12. MISSING CRITICAL DATA")
    missing_hour = [p for p in persons if p.get("birth_hour") is None]
    print(f"   Missing birth_hour: {len(missing_hour)} persons")
    missing_nat = [p for p in persons if not p.get("nationality")]
    print(f"   Missing nationality: {len(missing_nat)} persons")
    missing_source = [p for p in persons if not p.get("source")]
    print(f"   Missing source: {len(missing_source)} persons")

    print(f"\n{'='*60}")
    return {
        "persons": N, "events": E, "twin_groups": len(twin_groups),
        "occupations": len(occ_counter), "nationalities": len(nat_counter),
        "with_hour": has_hour, "with_bazi": has_bazi,
        "same_bazi_groups": len(multi),
        "duplicates": len(dupes),
        "year_range": f"{ymin}-{ymax}" if years else "N/A",
    }

if __name__ == "__main__":
    for fname in ["master_10k.json", "twins_collected.json", "seed_data.json", "generated_batch.json"]:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            audit(fpath)

    print("\n\nCROSS-FILE TOTALS:")
    all_persons = set()
    all_events = 0
    total_twin_groups = 0
    for fname in ["master_10k.json", "twins_collected.json", "seed_data.json"]:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
            for p in d.get("persons", []):
                all_persons.add(p.get("name", ""))
            all_events += len(d.get("events", []))
            total_twin_groups += len(d.get("twin_groups", {}))
    print(f"   Unique persons across all files: {len(all_persons):,}")
    print(f"   Total events across all files:   {all_events:,}")
    print(f"   Total twin groups across files:  {total_twin_groups:,}")
