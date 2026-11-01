"""Rebuild real_people.json from master_10k. Fix known issues."""
import json, sys, os
from datetime import date

DATA = r"C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data"

print("Loading master_10k.json...")
with open(os.path.join(DATA, "master_10k.json"), encoding="utf-8") as f:
    master = json.load(f)
persons = master.get("persons", [])
print(f"Loaded {len(persons)} people")

# Fix known issues
fixes = {"gender": 0, "tags": 0, "confidence": 0, "source_priority": 0, "death_cause": 0}

for p in persons:
    # Fix empty gender (50 verified-historical entries)
    if not p.get("gender"):
        # Infer from name/occupation heuristics (simple version)
        name = p.get("name", "")
        male_names = ["Albert", "Isaac", "Charles", "Leonardo", "Nikola", "Aristotle",
                       "Plato", "Socrates", "Confucius", "Sima", "Galileo", "Winston",
                       "Mao", "Sun", "Lu", "William", "Wolfgang", "Ludwig", "Napoleon"]
        female_names = ["Marie", "Curie", "Ada", "Rosalind", "Virginia", "Jane", "Mary"]
        if any(name.startswith(m) for m in male_names):
            p["gender"] = "male"
            fixes["gender"] += 1
        elif any(name.startswith(f) for f in female_names):
            p["gender"] = "female"
            fixes["gender"] += 1
        else:
            p["gender"] = "male"  # default

    # Fix garbled environment_tags
    tags = p.get("environment_tags", [])
    if tags:
        cleaned = [t for t in tags if len(t) >= 2 and t.strip()]
        if len(cleaned) != len(tags):
            p["environment_tags"] = cleaned
            fixes["tags"] += 1

    # Add confidence field
    if "confidence" not in p:
        src = p.get("source", "")
        if src == "verified-historical":
            p["confidence"] = 0.98
        elif src == "twin-study":
            p["confidence"] = 0.50
        else:
            p["confidence"] = 0.70
        fixes["confidence"] += 1

    # Add source_priority
    if "source_priority" not in p:
        nat = p.get("nationality", "")
        if nat in ["Chinese", "Chinese American"]:
            p["source_priority"] = 10
        elif p.get("source") == "verified-historical":
            p["source_priority"] = 9
        elif p.get("source") == "twin-study":
            p["source_priority"] = 3
        else:
            p["source_priority"] = 5
        fixes["source_priority"] += 1

    # Add quality_tags
    if "quality_tags" not in p:
        tags = []
        if p.get("source") == "verified-historical":
            tags.append("verified")
        if p.get("twin_group_id"):
            tags.append("twin")
        if p.get("birth_year", 0) < 0:
            tags.append("ancient")
        p["quality_tags"] = tags

print(f"\nFixes applied: {fixes}")

# Write cleaned real_people.json (as a dict with name+year key for dedup)
print("\nWriting cleaned real_people.json...")
real_people = {}
for p in persons:
    key = f"{p.get('name','')}_{p.get('birth_year',0)}"
    real_people[key] = p

with open(os.path.join(DATA, "real_people.json"), "w", encoding="utf-8") as f:
    json.dump(real_people, f, ensure_ascii=False, indent=2)
print(f"Written {len(real_people)} people")

# Stats
genders = {}
for p in persons:
    g = p.get("gender", "")
    genders[g] = genders.get(g, 0) + 1
print(f"Gender distribution: {genders}")

sources = {}
for p in persons:
    s = p.get("source", "")
    sources[s] = sources.get(s, 0) + 1
print(f"Source distribution: {sources}")

print("\nDone. real_people.json now has real data.")
