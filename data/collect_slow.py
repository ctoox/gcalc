"""
Multi-threaded global person collector.
Default: 10 threads, 5s batch delay = ~2 persons/sec.
Web-controllable: pause/resume/delay/threads/seek from persons panel.

Features:
- Singleton PID lock (one collector per machine)
- Graceful shutdown (finish in-flight before pausing)
- Deduplication by (name, birth_year)
- Idempotent API (rapid clicks don't cause issues)
"""

import sys, os, json, time, re, requests, threading, atexit
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from queue import Queue

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person
from data.control import read_control, write_control

DATA_DIR = os.path.dirname(__file__)
PID_FILE = os.path.join(DATA_DIR, "collector.pid")
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"
UA = "GCalc-Collector/1.0"

SPARQL_TPL = """
SELECT DISTINCT ?person ?name ?birth ?death ?occLabel ?natLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  OPTIONAL {{ ?person dbo:deathDate ?death . }}
  OPTIONAL {{ ?person dbo:occupation ?occ . }}
  OPTIONAL {{ ?person dbo:nationality ?nat . }}
  FILTER (lang(?name) = 'en')
}}
ORDER BY ?person
LIMIT 1 OFFSET {offset}
"""

SPARQL_CHINA = """
SELECT DISTINCT ?person ?name ?birth ?death ?occLabel ?natLabel WHERE {{
  ?person a dbo:Person .
  ?person foaf:name ?name .
  ?person dbo:birthDate ?birth .
  OPTIONAL {{ ?person dbo:deathDate ?death . }}
  OPTIONAL {{ ?person dbo:occupation ?occ . }}
  OPTIONAL {{ ?person dbo:nationality ?nat . }}
  FILTER (lang(?name) = 'en')
  ?nat rdfs:label ?natLabel .
  FILTER (contains(?natLabel, "China"))
}}
ORDER BY ?person
LIMIT 1 OFFSET {offset}
"""

def _parse_date(val):
    m = re.match(r"(\d{4})-?(\d{2})?-?(\d{2})?", str(val))
    if m:
        return {"year": int(m.group(1)), "month": int(m.group(2) or 1), "day": int(m.group(3) or 1)}
    return None

def _extract_label(uri):
    return uri.split("/")[-1].replace("_", " ") if uri else ""

class FastCollector:
    def __init__(self, state_file="slow_state.json"):
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

    def _acquire_lock(self):
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    old_pid = int(f.read().strip())
                if old_pid == os.getpid():
                    return True
                import subprocess
                r = subprocess.run(["tasklist", "/FI", f"PID eq {old_pid}", "/NH"],
                                   capture_output=True, text=True, timeout=5)
                if str(old_pid) in r.stdout:
                    print(f"[lock] Another collector already running (PID {old_pid}). Exiting.")
                    sys.exit(0)
            except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
                pass
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        atexit.register(self._release_lock)
        return True

    def _release_lock(self):
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                if pid == os.getpid():
                    os.remove(PID_FILE)
            except (ValueError, OSError):
                pass

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
                print(f"[fast] Loaded {len(d.get('persons',[]))} existing persons from disk")
            except Exception:
                pass
        self.total_collected = len(self.collector.persons)
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    s = json.load(f)
                self.next_offset = s.get("offset", 0)
                print(f"[fast] Resumed offset={self.next_offset} total={self.total_collected}")
            except Exception:
                pass
        self._sync_control()

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump({"offset": self.next_offset, "total": self.total_collected,
                       "updated": str(datetime.now())}, f)

    def _sync_control(self):
        ctrl = read_control()
        self.paused = ctrl.get("paused", False)
        self.delay = max(0.5, ctrl.get("delay_seconds", 5.0))
        self.threads = max(1, min(50, ctrl.get("threads", 10)))
        max_off = ctrl.get("max_offset", 0)
        if max_off > 0 and self.next_offset >= max_off:
            self.paused = True
            write_control({"paused": True})
        if ctrl.get("stop"):
            self._shutdown = True
            self.paused = True
            write_control({"paused": True, "stop": False})
        return ctrl

    def _get_next_offsets(self, n):
        with self.offset_lock:
            offsets = list(range(self.next_offset, self.next_offset + n))
            self.next_offset += n
            return offsets

    def fetch_one(self, offset, session):
        q = SPARQL_TPL.format(offset=offset)
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

    def run_batch(self):
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
                    fut = executor.submit(self.fetch_one, off, session)
                    fut_map[fut] = off
                for fut in as_completed(fut_map):
                    off = fut_map[fut]
                    person_data, err = fut.result()
                    if person_data:
                        results.append(person_data)
                    elif err:
                        pass

        added = 0
        for pd in results:
            key = (pd["name"], pd["birth"]["year"])
            if key in self._dedup_set:
                continue
            self._dedup_set.add(key)
            is_chinese = "china" in pd.get("nationality", "").lower()
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
                source="dbpedia-real",
                verified=True,
                confidence=0.95 if is_chinese else 0.9,
                source_priority=10 if is_chinese else 5,
            )
            self.collector.add_person(p)
            added += 1

        if added > 0:
            self.total_collected += added
            self.collector.export_json(os.path.join(DATA_DIR, "real_people.json"))
            # Also write to SQLite (no duplicates: INSERT OR REPLACE by name_year key)
            try:
                from core.db import get_db
                db = get_db()
                count = db.import_from_json(os.path.join(DATA_DIR, "real_people.json"))
                print(f"  sqlite: synced {count} people")
            except Exception as e:
                print(f"  sqlite sync failed: {e}")
            self._save_state()
            self._write_control()

        return added

    def _write_control(self):
        write_control({
            "offset": self.next_offset,
            "total": self.total_collected,
            "batch_speed": f"{self.total_collected / max(1, time.time() - self._start_time):.1f}/s" if hasattr(self, '_start_time') else "?",
        })

    def run(self, forever=True):
        self._acquire_lock()
        self._sync_control()
        self._start_time = time.time()
        print(f"[fast] Starting collector: {self.threads} threads, {self.delay}s batch delay")
        print(f"[fast] Resume offset={self.next_offset}, total={self.total_collected}")
        print(f"[fast] Control via http://127.0.0.1:20001/persons")
        try:
            while not self._shutdown:
                added = self.run_batch()
                if added == -1:
                    break
                rate = self.total_collected / max(1, time.time() - self._start_time)
                if added > 0:
                    print(f"[fast] +{added} persons (total={self.total_collected}, offset={self.next_offset}, {rate:.1f}/s)")
                self._sync_control()
                if self.delay > 0:
                    time.sleep(self.delay)
                if not forever:
                    break
        finally:
            self._save_state()
            write_control({"paused": True})
            self._release_lock()
            print(f"[fast] Stopped at offset={self.next_offset}, total={self.total_collected}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--delay", type=float, default=5.0)
    args = parser.parse_args()

    if args.threads or args.delay:
        write_control({"threads": args.threads, "delay_seconds": args.delay})

    fc = FastCollector()
    fc.run(forever=not args.once)
