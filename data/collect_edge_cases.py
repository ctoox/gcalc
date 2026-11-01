"""
Edge-case collector for fortune telling validation.
Collects: accidental deaths, twins, adoption errors, name collisions.
These are critical for validating prediction accuracy.
"""

import sys, os, json, time, re, requests, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person
from data.control import read_control, write_control

DATA_DIR = os.path.dirname(__file__)
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"
UA = "GCalc-EdgeCollector/1.0"

SPARQL_ACCIDENTAL_DEATH = """
SELECT DISTINCT ?person ?name ?birth ?death ?causeLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  ?person dbo:deathDate ?death .
  OPTIONAL {{ ?person dbo:deathCause ?cause . }}
  FILTER (lang(?name) = 'en')
  FILTER (?death >= "1900-01-01"^^xsd:date)
  FILTER (contains(lcase(str(?cause)), "accident") 
       || contains(lcase(str(?cause)), "crash") 
       || contains(lcase(str(?cause)), "collision")
       || contains(lcase(str(?cause)), "drown")
       || contains(lcase(str(?cause)), "fire")
       || contains(lcase(str(?cause)), "explosion"))
}}
ORDER BY ?death DESC
LIMIT 1 OFFSET {offset}
"""

SPARQL_TWINS_SAME_BIRTH = """
SELECT DISTINCT ?person1 ?name1 ?birth1 ?person2 ?name2 ?birth2 WHERE {{
  ?person1 a dbo:Person .
  ?person1 foaf:name ?name1 .
  ?person1 dbo:birthDate ?birth1 .
  ?person2 a dbo:Person .
  ?person2 foaf:name ?name2 .
  ?person2 dbo:birthDate ?birth2 .
  OPTIONAL {{ ?person1 dbo:deathDate ?death1 . }}
  OPTIONAL {{ ?person2 dbo:deathDate ?death2 . }}
  FILTER (?person1 != ?person2)
  FILTER (?birth1 = ?birth2)
  FILTER (lang(?name1) = 'en')
  FILTER (lang(?name2) = 'en')
}}
LIMIT 5 OFFSET {offset}
"""

SPARQL_YOUNG_DEATH = """
SELECT DISTINCT ?person ?name ?birth ?death ?occLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  ?person dbo:deathDate ?death .
  OPTIONAL {{ ?person dbo:occupation ?occ . }}
  FILTER (lang(?name) = 'en')
  BIND(year(?death) - year(?birth) AS ?age)
  FILTER (?age < 30)
  FILTER (?death >= "1900-01-01"^^xsd:date)
}}
ORDER BY ?death DESC
LIMIT 1 OFFSET {offset}
"""

SPARQL_ADOPTED_PERSONS = """
SELECT DISTINCT ?person ?name ?birth ?death ?occLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  OPTIONAL {{ ?person dbo:deathDate ?death . }}
  OPTIONAL {{ ?person dbo:occupation ?occ . }}
  FILTER (lang(?name) = 'en')
  FILTER (contains(lcase(str(?person)), "adopt") 
       || contains(lcase(str(?name)), "adopt"))
}}
ORDER BY ?person
LIMIT 1 OFFSET {offset}
"""

SPARQL名人_SAME_NAME = """
SELECT DISTINCT ?person1 ?name1 ?birth1 ?person2 ?name2 ?birth2 WHERE {{
  ?person1 a dbo:Person .
  ?person1 foaf:name ?name1 .
  ?person1 dbo:birthDate ?birth1 .
  ?person2 a dbo:Person .
  ?person2 foaf:name ?name2 .
  ?person2 dbo:birthDate ?birth2 .
  FILTER (?person1 != ?person2)
  FILTER (?name1 = ?name2)
  FILTER (lang(?name1) = 'en')
  FILTER (year(?birth1) != year(?birth2))
}}
LIMIT 5 OFFSET {offset}
"""

SPARQL_MURDER = """
SELECT DISTINCT ?person ?name ?birth ?death ?causeLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  ?person dbo:deathDate ?death .
  OPTIONAL {{ ?person dbo:deathCause ?cause . }}
  FILTER (lang(?name) = 'en')
  FILTER (contains(lcase(str(?cause)), "murder") 
       || contains(lcase(str(?cause)), "assassin") 
       || contains(lcase(str(?cause)), "kill"))
}}
ORDER BY ?death DESC
LIMIT 1 OFFSET {offset}
"""

SPARQL_SUICIDE = """
SELECT DISTINCT ?person ?name ?birth ?death ?causeLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  ?person dbo:deathDate ?death .
  OPTIONAL {{ ?person dbo:deathCause ?cause . }}
  FILTER (lang(?name) = 'en')
  FILTER (contains(lcase(str(?cause)), "suicide"))
}}
ORDER BY ?death DESC
LIMIT 1 OFFSET {offset}
"""

SPARQL_NATURAL_DISASTER = """
SELECT DISTINCT ?person ?name ?birth ?death ?causeLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  ?person dbo:deathDate ?death .
  OPTIONAL {{ ?person dbo:deathCause ?cause . }}
  FILTER (lang(?name) = 'en')
  FILTER (contains(lcase(str(?cause)), "earthquake") 
       || contains(lcase(str(?cause)), "tsunami") 
       || contains(lcase(str(?cause)), "flood")
       || contains(lcase(str(?cause)), "hurricane")
       || contains(lcase(str(?cause)), "tornado"))
}}
ORDER BY ?death DESC
LIMIT 1 OFFSET {offset}
"""

QUERIES = {
    "accidental_death": (SPARQL_ACCIDENTAL_DEATH, "accidental_death", 20),
    "twins": (SPARQL_TWINS_SAME_BIRTH, "twin_pair", 15),
    "young_death": (SPARQL_YOUNG_DEATH, "young_death", 15),
    "adopted": (SPARQL_ADOPTED_PERSONS, "adopted", 5),
    "same_name": (SPARQL名人_SAME_NAME, "name_collision", 10),
    "murder": (SPARQL_MURDER, "murder", 10),
    "suicide": (SPARQL_SUICIDE, "suicide", 5),
    "natural_disaster": (SPARQL_NATURAL_DISASTER, "natural_disaster", 5),
}

def _parse_date(val):
    m = re.match(r"(\d{4})-?(\d{2})?-?(\d{2})?", str(val))
    if m:
        return {"year": int(m.group(1)), "month": int(m.group(2) or 1), "day": int(m.group(3) or 1)}
    return None

def _extract_label(uri):
    return uri.split("/")[-1].replace("_", " ") if uri else ""

class EdgeCaseCollector:
    def __init__(self, state_file="edge_state.json"):
        self.state_file = os.path.join(DATA_DIR, state_file)
        self.collector = DataCollector()
        self.offset_lock = threading.Lock()
        self.offsets = {}
        self.total_collected = 0
        self.paused = False
        self.delay = 5.0
        self.threads = 10
        self._shutdown = False
        self._dedup_set = set()
        self._load_state()

    def _load_state(self):
        real_file = os.path.join(DATA_DIR, "real_people.json")
        if os.path.exists(real_file):
            try:
                with open(real_file, "r", encoding="utf-8") as f:
                    d = json.load(f)
                for pd in d.get("persons", []):
                    try:
                        p = Person(**{k: v for k, v in pd.items()
                                    if k in Person.__dataclass_fields__ and v is not None})
                        self.collector.add_person(p)
                        key = (pd.get("name",""), pd.get("birth_year"))
                        if key[0]:
                            self._dedup_set.add(key)
                    except Exception:
                        pass
                print(f"[edge] Loaded {len(d.get('persons',[]))} existing persons from disk")
            except Exception:
                pass
        self.total_collected = len(self.collector.persons)
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    s = json.load(f)
                self.offsets = s.get("offsets", {})
                print(f"[edge] Resumed offsets={self.offsets} total={self.total_collected}")
            except Exception:
                pass

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"offsets": self.offsets, "total": self.total_collected,
                       "updated": str(datetime.now())}, f)

    def _sync_control(self):
        ctrl = read_control()
        self.paused = ctrl.get("paused", False)
        self.delay = max(0.5, ctrl.get("delay_seconds", 5.0))
        self.threads = max(1, min(50, ctrl.get("threads", 10)))
        if ctrl.get("stop"):
            self._shutdown = True
            self.paused = True
        return ctrl

    def _get_next_offset(self, category):
        with self.offset_lock:
            off = self.offsets.get(category, 0)
            self.offsets[category] = off + 1
            return off

    def fetch_one(self, offset, session, query_template):
        q = query_template.format(offset=offset)
        try:
            resp = session.get(DBPEDIA_SPARQL, params={"format": "json", "query": q},
                              headers={"User-Agent": UA}, timeout=120)
            if resp.status_code == 429:
                return None, f"429 offset={offset}"
            if resp.status_code != 200:
                return None, f"HTTP {resp.status_code}"
            data = resp.json()
            bindings = data["results"]["bindings"]
            if not bindings:
                return None, f"empty offset={offset}"
            r = bindings[0]
            name = r.get("name", {}).get("value", "").strip()
            birth = _parse_date(r.get("birth", {}).get("value", ""))
            death = _parse_date(r.get("death", {}).get("value", ""))
            if not birth or not name:
                return None, f"no-name offset={offset}"
            if not (1500 <= birth["year"] <= 2026):
                return None, f"year={birth['year']}"
            occ = r.get("occLabel", {}).get("value", "")
            if not occ:
                occ_uri = r.get("occ", {}).get("value", "")
                occ = _extract_label(occ_uri)
            cause = r.get("causeLabel", {}).get("value", "")
            return {
                "name": name, "birth": birth, "death": death,
                "occupation": occ, "cause": cause,
            }, None
        except Exception as e:
            return None, str(e)

    def run_batch(self):
        self._sync_control()
        if self.paused:
            if self._shutdown:
                return -1
            time.sleep(2)
            return 0

        added = 0
        for cat, (query, tag, count) in QUERIES.items():
            if added >= self.threads:
                break
            offset = self._get_next_offset(cat)
            try:
                with requests.Session() as session:
                    person_data, err = self.fetch_one(offset, session, query)
                    if person_data:
                        key = (person_data["name"], person_data["birth"]["year"])
                        if key not in self._dedup_set:
                            self._dedup_set.add(key)
                            p = Person(
                                name=person_data["name"],
                                birth_year=person_data["birth"]["year"],
                                birth_month=person_data["birth"]["month"],
                                birth_day=person_data["birth"]["day"],
                                death_year=person_data["death"]["year"] if person_data["death"] else None,
                                death_month=person_data["death"]["month"] if person_data["death"] else None,
                                death_day=person_data["death"]["day"] if person_data["death"] else None,
                                occupation=person_data.get("occupation", ""),
                                source=f"dbpedia-{tag}",
                                verified=True,
                                confidence=0.85,
                                quality_tags=[tag],
                                death_cause=person_data.get("cause", ""),
                                source_priority=5,
                            )
                            self.collector.add_person(p)
                            added += 1
            except Exception as e:
                pass

        if added > 0:
            self.total_collected += added
            self.collector.export_json(os.path.join(DATA_DIR, "real_people.json"))
            self._save_state()

        return added

    def run(self, forever=True):
        self._sync_control()
        self._start_time = time.time()
        print(f"[edge] Starting edge-case collector: {self.threads} threads, {self.delay}s delay")
        try:
            while not self._shutdown:
                added = self.run_batch()
                if added == -1:
                    break
                rate = self.total_collected / max(1, time.time() - self._start_time)
                if added > 0:
                    print(f"[edge] +{added} edge cases (total={self.total_collected}, {rate:.1f}/s)")
                self._sync_control()
                if self.delay > 0:
                    time.sleep(self.delay)
                if not forever:
                    break
        finally:
            self._save_state()
            print(f"[edge] Stopped, total={self.total_collected}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--delay", type=float, default=8.0)
    args = parser.parse_args()

    fc = EdgeCaseCollector()
    fc.run(forever=not args.once)
