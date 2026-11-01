"""
Global Real Person Data Collector
Sources: DBpedia SPARQL (primary), MusicBrainz (secondary)
Collects real verified human biographical data from the open web.
"""

import sys, os, json, time, re, requests
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person, LifeEvent

DATA_DIR = os.path.dirname(__file__)
DBPEDIA_SPARQL = "https://dbpedia.org/sparql"
DBPEDIA_DATA = "https://dbpedia.org/data"
MUSICBRAINZ = "https://musicbrainz.org/ws/2"

UA = "GCalc-Collector/1.0 (global human records)"
DELAY = 2.0
LAST_REQ = 0.0

def rate_limit():
    global LAST_REQ
    e = time.time() - LAST_REQ
    if e < DELAY:
        time.sleep(DELAY - e)
    LAST_REQ = time.time()

def dbpedia_query(sparql, timeout=120):
    rate_limit()
    try:
        resp = requests.get(DBPEDIA_SPARQL, params={"format": "json", "query": sparql},
                          headers={"User-Agent": UA}, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"[dbpedia] HTTP {resp.status_code}")
            return None
    except Exception as e:
        print(f"[dbpedia] Error: {e}")
        return None

def extract_label(uri):
    return uri.split("/")[-1].replace("_", " ") if uri else ""

def parse_dbpediadate(val):
    if not val:
        return None
    m = re.match(r"(\d{4})-?(\d{2})?-?(\d{2})?", str(val))
    if m:
        y = int(m.group(1))
        if 1500 <= y <= 2026:
            return {"year": y, "month": int(m.group(2) or 1), "day": int(m.group(3) or 1)}
    return None

def fetch_people_batch(offset=0, limit=500):
    q = f"""
    SELECT DISTINCT ?person ?name ?birth ?death ?occ ?occLabel ?nat ?natLabel WHERE {{
      ?person a dbo:Person .
      ?person foaf:name ?name .
      ?person dbo:birthDate ?birth .
      OPTIONAL {{ ?person dbo:deathDate ?death . }}
      OPTIONAL {{ ?person dbo:occupation ?occ . }}
      OPTIONAL {{ ?person dbo:nationality ?nat . }}
      FILTER (lang(?name) = 'en')
    }}
    ORDER BY ?person
    LIMIT {limit} OFFSET {offset}
    """
    data = dbpedia_query(q)
    if not data:
        return []
    bindings = data["results"]["bindings"]
    seen = set()
    results = []
    for r in bindings:
        person_url = r.get("person", {}).get("value", "")
        if person_url in seen:
            continue
        seen.add(person_url)
        name = r.get("name", {}).get("value", "").strip()
        birth = parse_dbpediadate(r.get("birth", {}).get("value", ""))
        death = parse_dbpediadate(r.get("death", {}).get("value", ""))
        occ_uri = r.get("occ", {}).get("value", "")
        occ_label = r.get("occLabel", {}).get("value", "") or extract_label(occ_uri)
        nat_uri = r.get("nat", {}).get("value", "")
        nat_label = r.get("natLabel", {}).get("value", "") or extract_label(nat_uri)
        if not birth:
            continue
        results.append({
            "name": name,
            "birth": birth,
            "death": death,
            "occupation": occ_label,
            "nationality": nat_label,
            "source": "dbpedia",
            "verified": True,
        })
    return results

def fetch_person_detail(name):
    encoded = name.replace(" ", "_")
    url = f"{DBPEDIA_DATA}/{encoded}.json"
    rate_limit()
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            uri = f"http://dbpedia.org/resource/{encoded}"
            if uri in data:
                info = data[uri]
                result = {"name": name}
                birth = info.get("http://dbpedia.org/ontology/birthDate", [{}])
                if birth:
                    result["birth"] = birth[0].get("value", "")
                death = info.get("http://dbpedia.org/ontology/deathDate", [{}])
                if death:
                    result["death"] = death[0].get("value", "")
                occs = info.get("http://dbpedia.org/ontology/occupation", [])
                if occs:
                    result["occupations"] = [o.get("value", "") for o in occs[:3]]
                return result
    except Exception as e:
        pass
    return None

def collect_from_musicbrainz(offset=0, limit=100):
    params = {
        "query": "BEGIN",
        "limit": limit,
        "offset": offset,
        "fmt": "json",
    }
    rate_limit()
    try:
        resp = requests.get(f"{MUSICBRAINZ}/artist/", params=params,
                          headers={"User-Agent": UA}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for artist in data.get("artists", []):
                name = artist.get("name", "")
                life = artist.get("life-span", {})
                birth = life.get("begin", "")
                death = life.get("end", "")
                bd = parse_dbpediadate(birth)
                if bd and bd["year"] >= 1500:
                    results.append({
                        "name": name,
                        "birth": bd,
                        "death": parse_dbpediadate(death) if death else None,
                        "occupation": "musician",
                        "nationality": "",
                        "source": "musicbrainz",
                        "verified": True,
                    })
            return results
    except Exception as e:
        print(f"[musicbrainz] Error: {e}")
    return []

class RealDataCollector:
    def __init__(self):
        self.collector = DataCollector()
        self.stats = {"dbpedia": 0, "musicbrainz": 0, "total": 0}

    def run_dbpedia(self, target=10000, batch=500):
        offset = 0
        total = 0
        failures = 0
        while total < target and failures < 5:
            print(f"[real] DBpedia offset={offset}...")
            people = fetch_people_batch(offset, batch)
            if not people:
                failures += 1
                offset += batch
                continue
            failures = 0
            for p in people:
                person = Person(
                    name=p["name"],
                    birth_year=p["birth"]["year"],
                    birth_month=p["birth"]["month"],
                    birth_day=p["birth"]["day"],
                    death_year=p["death"]["year"] if p["death"] else None,
                    death_month=p["death"]["month"] if p["death"] else None,
                    death_day=p["death"]["day"] if p["death"] else None,
                    nationality=p.get("nationality", ""),
                    occupation=p.get("occupation", ""),
                    source="dbpedia",
                    verified=True,
                )
                self.collector.add_person(person)
                total += 1
            self.stats["dbpedia"] = total
            self.stats["total"] = total
            if total % 1000 == 0:
                print(f"[real] DBpedia progress: {total} persons")
            offset += batch
        return total

    def run_musicbrainz(self, target=2000, batch=100):
        offset = 0
        total = 0
        failures = 0
        while total < target and failures < 5:
            artists = collect_from_musicbrainz(offset, batch)
            if not artists:
                failures += 1
                offset += batch
                continue
            failures = 0
            for a in artists:
                person = Person(
                    name=a["name"],
                    birth_year=a["birth"]["year"],
                    birth_month=a["birth"]["month"],
                    birth_day=a["birth"]["day"],
                    death_year=a["death"]["year"] if a["death"] else None,
                    death_month=a["death"]["month"] if a["death"] else None,
                    death_day=a["death"]["day"] if a["death"] else None,
                    nationality=a.get("nationality", ""),
                    occupation=a.get("occupation", "musician"),
                    source="musicbrainz",
                    verified=True,
                )
                self.collector.add_person(person)
                total += 1
            self.stats["musicbrainz"] = total
            self.stats["total"] = self.stats["dbpedia"] + total
            offset += batch
        return total

    def export(self, filename="real_people.json"):
        out = os.path.join(DATA_DIR, filename)
        self.collector.export_json(out)
        print(f"[real] Exported {self.collector.summary()}")
        return out

    def summary(self):
        return self.stats

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Global real person collector")
    parser.add_argument("--dbpedia", type=int, default=5000, help="Target DBpedia count")
    parser.add_argument("--musicbrainz", type=int, default=1000, help="Target MusicBrainz count")
    parser.add_argument("--output", default="real_people.json", help="Output filename")
    args = parser.parse_args()

    print(f"[real] Starting collection: DBpedia={args.dbpedia}, MusicBrainz={args.musicbrainz}")
    rc = RealDataCollector()

    if args.dbpedia > 0:
        print(f"\n{'='*50}")
        print(f"COLLECTING FROM DBPEDIA (target: {args.dbpedia})")
        print(f"{'='*50}")
        t1 = time.time()
        count = rc.run_dbpedia(args.dbpedia)
        elapsed = time.time() - t1
        print(f"DBpedia done: {count} persons in {elapsed:.0f}s ({count/elapsed:.1f}/s)")

    if args.musicbrainz > 0:
        print(f"\n{'='*50}")
        print(f"COLLECTING FROM MUSICBRAINZ (target: {args.musicbrainz})")
        print(f"{'='*50}")
        t1 = time.time()
        count = rc.run_musicbrainz(args.musicbrainz)
        elapsed = time.time() - t1
        print(f"MusicBrainz done: {count} persons in {elapsed:.0f}s ({count/elapsed:.1f}/s)")

    rc.export(args.output)
    print(f"\nFinal: {rc.summary()}")
