import json

d = json.load(open("data/master_10k.json", encoding="utf-8"))
s = d["summary"]
print(f"Persons: {s['total_persons']}")
print(f"Events: {s['total_events']}")
print(f"Twin groups: {s['total_twin_groups']}")
print(f"Twin persons: {s['twin_persons']}")
print(f"Sources: {s['sources']}")

persons = d["persons"]
occ_counts = {}
for p in persons:
    occ = p.get("occupation", "unknown")
    occ_counts[occ] = occ_counts.get(occ, 0) + 1

nat_counts = {}
for p in persons:
    nat = p.get("nationality", "unknown")
    nat_counts[nat] = nat_counts.get(nat, 0) + 1

print(f"Unique occupations: {len(occ_counts)}")
print(f"Nationalities: {len(nat_counts)}")
print(f"Top 10 occupations:")
for occ, cnt in sorted(occ_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {occ}: {cnt}")
print(f"Top 10 nationalities:")
for nat, cnt in sorted(nat_counts.items(), key=lambda x: -x[1])[:10]:
    print(f"  {nat}: {cnt}")

twins = d.get("twin_groups", {})
print(f"Twin groups in data: {len(twins)}")
if twins:
    first_key = list(twins.keys())[0]
    print(f"  Sample: {first_key} -> {twins[first_key]}")
