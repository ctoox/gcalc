import sys
import os
import json
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person, LifeEvent

OCCUPATIONS = ["scientist", "artist", "writer", "philosopher", "politician", "musician"]
NATIONALITIES = ["Chinese", "German", "French", "English", "Italian", "American", "Russian", "Japanese"]
EVENT_TEMPLATES = {
    "education": [
        "Enrolled at {institution}",
        "Graduated from {institution} with honors",
        "Received scholarship to study at {institution}",
    ],
    "achievement": [
        "Published seminal work on {topic}",
        "Made breakthrough discovery in {field}",
        "Developed revolutionary {method}",
    ],
    "award": [
        "Received {prize} for contributions to {field}",
        "Honored with {title} by {organization}",
        "Elected to {academy}",
    ],
    "position": [
        "Appointed {role} at {organization}",
        "Founded {institution}",
        "Served as {title}",
    ],
    "migration": [
        "Relocated to {city}",
        "Exiled from {country}",
        "Emigrated to {country}",
    ],
    "publication": [
        "Published {work}",
        "Completed {masterpiece}",
        "Released {opus}",
    ],
}

FILL_VALUES = {
    "institution": ["Cambridge", "Oxford", "Sorbonne", "MIT", "Tsinghua", "Heidelberg", "Göttingen"],
    "topic": ["quantum mechanics", "relativity", "evolution", "electromagnetism", "thermodynamics", "genetics"],
    "field": ["physics", "chemistry", "biology", "mathematics", "philosophy", "literature", "medicine"],
    "method": ["analytical framework", "experimental protocol", "theoretical model", "computational algorithm"],
    "prize": ["Nobel Prize", "Fields Medal", "Pulitzer Prize", "Academy Award", "National Medal of Science"],
    "title": ["Professor Emeritus", "Chair of Department", "Royal Advisor", "Chief Scientist"],
    "organization": ["Royal Society", "National Academy", "University College", "Research Institute"],
    "academy": ["Royal Society", "National Academy of Sciences", "Academy of Arts and Sciences"],
    "role": ["Department Chair", "Research Director", "Principal Investigator", "Dean"],
    "institution": ["research center", "academy", "university", "laboratory"],
    "city": ["Paris", "Berlin", "London", "New York", "Vienna", "Beijing", "Tokyo"],
    "country": ["France", "Germany", "England", "United States", "Japan", "China"],
    "work": ["first monograph", "landmark paper", "comprehensive treatise", "critical essay"],
    "masterpiece": ["magnum opus", "definitive work", "foundational text"],
    "opus": ["symphony", "novel", "art collection", "poetry anthology"],
}

NAME_POOLS = {
    "scientist": [
        ("Niels Bohr", "Danish"), ("Max Planck", "German"), ("Erwin Schrödinger", "Austrian"),
        ("Werner Heisenberg", "German"), ("Paul Dirac", "English"), ("Enrico Fermi", "Italian"),
        ("Richard Feynman", "American"), ("Stephen Hawking", "English"), ("James Clerk Maxwell", "Scottish"),
        ("Michael Faraday", "English"), ("Dmitri Mendeleev", "Russian"), ("Gregor Mendel", "Austrian"),
        ("Louis Pasteur", "French"), ("Ada Lovelace", "English"), ("Rosalind Franklin", "English"),
    ],
    "philosopher": [
        ("Plato", "Greek"), ("Aristotle", "Greek"), ("Socrates", "Greek"),
        ("Immanuel Kant", "German"), ("Friedrich Nietzsche", "German"),
        ("Jean-Jacques Rousseau", "French"), ("John Locke", "English"),
        ("David Hume", "Scottish"), ("Zhuangzi", "Chinese"), ("Wang Yangming", "Chinese"),
    ],
    "writer": [
        ("William Shakespeare", "English"), ("Leo Tolstoy", "Russian"),
        ("Fyodor Dostoevsky", "Russian"), ("Franz Kafka", "Czech"),
        ("James Joyce", "Irish"), ("Lu Xun", "Chinese"), ("Cao Xueqin", "Chinese"),
    ],
    "artist": [
        ("Michelangelo", "Italian"), ("Vincent van Gogh", "Dutch"),
        ("Pablo Picasso", "Spanish"), ("Rembrandt", "Dutch"),
        ("Claude Monet", "French"), ("Zhang Daqian", "Chinese"), ("Qi Baishi", "Chinese"),
    ],
}

def generate_person_and_events(name, nationality, occupation, base_year):
    birth_year = base_year
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    lifespan = random.randint(60, 90)
    death_year = birth_year + lifespan

    person = Person(
        name=name,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        death_year=death_year,
        death_month=random.randint(1, 12),
        death_day=random.randint(1, 28),
        nationality=nationality,
        occupation=occupation,
        source="generated",
        verified=False,
    )

    events = []
    adult_years = list(range(birth_year + 20, death_year - 5))
    random.shuffle(adult_years)
    num_events = min(random.randint(4, 8), len(adult_years))
    event_types = list(EVENT_TEMPLATES.keys())

    for i in range(num_events):
        year = adult_years[i]
        etype = event_types[i % len(event_types)]
        templates = EVENT_TEMPLATES[etype]
        template = random.choice(templates)
        description = template.format(**{k: random.choice(v) for k, v in FILL_VALUES.items()})

        events.append(LifeEvent(
            person_name=name,
            year=year,
            month=random.randint(1, 12),
            day=random.randint(1, 28),
            event_type=etype,
            description=description,
            source="generated",
            verified=False,
        ))

    events.append(LifeEvent(
        person_name=name,
        year=death_year,
        month=person.death_month or 1,
        day=person.death_day or 1,
        event_type="death",
        description=f"{name} passed away at age {lifespan}",
        source="generated",
        verified=False,
    ))

    return person, events

def batch_generate(target_persons=30):
    collector = DataCollector()
    all_names = []
    for occ, names in NAME_POOLS.items():
        for name, nat in names:
            all_names.append((name, nat, occ))

    random.shuffle(all_names)
    used = min(target_persons, len(all_names))

    for i, (name, nat, occ) in enumerate(all_names[:used]):
        base_year = random.choice([1810, 1830, 1850, 1870, 1880, 1900, 1920, 1940, 1960])
        person, events = generate_person_and_events(name, nat, occ, base_year)
        collector.add_person_with_events(person, events)

    out_path = os.path.join(os.path.dirname(__file__), "generated_batch.json")
    collector.export_json(out_path)
    print(f"[batch] Generated {used} persons with events -> {out_path}")
    return collector

def merge_all(output="persons_merged.json"):
    seed_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    wiki_path = os.path.join(os.path.dirname(__file__), "wikipedia_celebrities.json")
    batch_path = os.path.join(os.path.dirname(__file__), "generated_batch.json")

    collector = DataCollector()
    for fp in [seed_path, wiki_path, batch_path]:
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            for pd in data.get("persons", []):
                p = Person(**{k: v for k, v in pd.items() if k in Person.__dataclass_fields__})
                collector.add_person(p)
            for ed in data.get("events", []):
                e = LifeEvent(**{k: v for k, v in ed.items() if k in LifeEvent.__dataclass_fields__})
                collector.add_event(e)

    out = os.path.join(os.path.dirname(__file__), output)
    collector.export_json(out)
    print(f"[batch] Merged: {collector.summary()}")
    return collector

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=30, help="Number of persons to generate")
    parser.add_argument("--merge", action="store_true", help="Merge all data sources")
    args = parser.parse_args()

    if args.merge:
        merge_all()
    else:
        batch_generate(args.count)
