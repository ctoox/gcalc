"""
Chinese-focused person collector.
Queries DBpedia for Chinese nationals with Chinese names.
Uses SPARQL to filter by nationality and language.
"""

import sys, os, json, time, re, requests, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person
from data.control import read_control, write_control

DATA_DIR = os.path.dirname(__file__)
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"
UA = "GCalc-ChinaCollector/1.0"

SPARQL_CHINA = """
SELECT DISTINCT ?person ?name ?birth ?death ?occLabel ?natLabel ?birthPlaceLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  OPTIONAL {{ ?person dbo:deathDate ?death . }}
  OPTIONAL {{ ?person dbo:occupation ?occ . }}
  OPTIONAL {{ ?person dbo:nationality ?nat . }}
  OPTIONAL {{ ?person dbo:birthPlace ?birthPlace . }}
  FILTER (lang(?name) = 'en')
  ?nat rdfs:label ?natLabel .
  FILTER (contains(?natLabel, "China"))
}}
ORDER BY ?person
LIMIT 1 OFFSET {offset}
"""

SPARQL_CHINESE_NAMES = """
SELECT DISTINCT ?person ?name ?birth ?death ?occLabel WHERE {{
  ?person a dbo:Person .
  {{ ?person foaf:name ?name . FILTER (lang(?name) = 'zh') }}
  UNION
  {{ ?person rdfs:label ?name . FILTER (lang(?name) = 'zh') }}
  ?person dbo:birthDate ?birth .
  OPTIONAL {{ ?person dbo:deathDate ?death . }}
  OPTIONAL {{ ?person dbo:occupation ?occ . }}
  FILTER (regex(?name, "[\\x{4e00}-\\x{9fff}]"))
}}
ORDER BY ?person
LIMIT 1 OFFSET {offset}
"""

SPARQL_DEATH_CAUSE = """
SELECT DISTINCT ?person ?name ?birth ?death ?causeLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  ?person dbo:deathDate ?death .
  OPTIONAL {{ ?person dbo:deathCause ?cause . }}
  FILTER (lang(?name) = 'en')
  FILTER (?death >= "2000-01-01"^^xsd:date)
}}
ORDER BY ?death DESC
LIMIT 1 OFFSET {offset}
"""

SPARQL_TWINS = """
SELECT DISTINCT ?person1 ?name1 ?birth1 ?person2 ?name2 ?birth2 WHERE {{
  ?person1 a dbo:Person .
  ?person1 foaf:name ?name1 .
  ?person1 dbo:birthDate ?birth1 .
  ?person2 a dbo:Person .
  ?person2 foaf:name ?name2 .
  ?person2 dbo:birthDate ?birth2 .
  FILTER (?person1 != ?person2)
  FILTER (?birth1 = ?birth2)
  FILTER (lang(?name1) = 'en')
  FILTER (lang(?name2) = 'en')
}}
LIMIT 10 OFFSET {offset}
"""

def _parse_date(val):
    m = re.match(r"(\d{4})-?(\d{2})?-?(\d{2})?", str(val))
    if m:
        return {"year": int(m.group(1)), "month": int(m.group(2) or 1), "day": int(m.group(3) or 1)}
    return None

def _extract_label(uri):
    return uri.split("/")[-1].replace("_", " ") if uri else ""

class ChinaCollector:
    def __init__(self, state_file="china_state.json"):
        self.state_file = os.path.join(DATA_DIR, state_file)
        self.collector = DataCollector()
        self.offset_lock = threading.Lock()
        self.next_offset = 0
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
                print(f"[china] Loaded {len(d.get('persons',[]))} existing persons from disk")
            except Exception:
                pass
        self.total_collected = len(self.collector.persons)
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    s = json.load(f)
                self.next_offset = s.get("offset", 0)
                print(f"[china] Resumed offset={self.next_offset} total={self.total_collected}")
            except Exception:
                pass

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"offset": self.next_offset, "total": self.total_collected,
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

    def _get_next_offsets(self, n):
        with self.offset_lock:
            offsets = list(range(self.next_offset, self.next_offset + n))
            self.next_offset += n
            return offsets

    def fetch_one(self, offset, session, query_template=SPARQL_CHINA):
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
            nat = r.get("natLabel", {}).get("value", "")
            if not nat:
                nat_uri = r.get("nat", {}).get("value", "")
                nat = _extract_label(nat_uri)
            return {
                "name": name, "birth": birth, "death": death,
                "occupation": occ, "nationality": nat,
            }, None
        except Exception as e:
            return None, str(e)

    def run_batch(self, query_template=SPARQL_CHINA):
        self._sync_control()
        if self.paused:
            if self._shutdown:
                return -1
            time.sleep(2)
            return 0

        n = self.threads
        offsets = self._get_next_offsets(n)
        if not offsets:
            time.sleep(1)
            return 0

        results = []
        with ThreadPoolExecutor(max_workers=n) as executor:
            fut_map = {}
            with requests.Session() as session:
                for off in offsets:
                    fut = executor.submit(self.fetch_one, off, session, query_template)
                    fut_map[fut] = off
                for fut in as_completed(fut_map):
                    off = fut_map[fut]
                    person_data, err = fut.result()
                    if person_data:
                        results.append(person_data)

        added = 0
        for pd in results:
            key = (pd["name"], pd["birth"]["year"])
            if key in self._dedup_set:
                continue
            self._dedup_set.add(key)
            p = Person(
                name=pd["name"],
                birth_year=pd["birth"]["year"],
                birth_month=pd["birth"]["month"],
                birth_day=pd["birth"]["day"],
                death_year=pd["death"]["year"] if pd["death"] else None,
                death_month=pd["death"]["month"] if pd["death"] else None,
                death_day=pd["death"]["day"] if pd["death"] else None,
                nationality=pd.get("nationality", ""),
                occupation=pd.get("occupation", ""),
                source="dbpedia-china",
                verified=True,
                confidence=0.9,
                source_priority=10,
            )
            self.collector.add_person(p)
            added += 1

        if added > 0:
            self.total_collected += added
            self.collector.export_json(os.path.join(DATA_DIR, "real_people.json"))
            self._save_state()

        return added

    def run(self, forever=True):
        self._sync_control()
        self._start_time = time.time()
        print(f"[china] Starting Chinese collector: {self.threads} threads, {self.delay}s delay")
        try:
            while not self._shutdown:
                added = self.run_batch()
                if added == -1:
                    break
                rate = self.total_collected / max(1, time.time() - self._start_time)
                if added > 0:
                    print(f"[china] +{added} Chinese persons (total={self.total_collected}, offset={self.next_offset}, {rate:.1f}/s)")
                self._sync_control()
                if self.delay > 0:
                    time.sleep(self.delay)
                if not forever:
                    break
        finally:
            self._save_state()
            print(f"[china] Stopped at offset={self.next_offset}, total={self.total_collected}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--delay", type=float, default=5.0)
    args = parser.parse_args()

    if args.threads or args.delay:
        write_control({"threads": args.threads, "delay_seconds": args.delay})

    fc = ChinaCollector()
    fc.run(forever=not args.once)
