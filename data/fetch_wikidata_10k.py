import sys, os, json, time, requests, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person, LifeEvent

WDQ = "https://query.wikidata.org/sparql"
PROXIES = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}
USE_PROXY = True
DELAY = 1.5
DATA_DIR = os.path.join(os.path.dirname(__file__))
_LAST = 0.0

def _rl():
    global _LAST
    e = time.time() - _LAST
    if e < DELAY:
        time.sleep(DELAY - e)
    _LAST = time.time()

def _px():
    return PROXIES if USE_PROXY else None

def parse_wd_date(val):
    if not val:
        return None
    m = re.match(r"[+-]?(\d{4})(?:-(\d{2})(?:-(\d{2})?)?)?", val)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2)) if m.group(2) and m.group(2) != "00" else 1
        d = int(m.group(3)) if m.group(3) and m.group(3) != "00" else 1
        if 1500 <= y <= 2026:
            return {"year": y, "month": mo, "day": d}
    return None

QUERY_TPL = """SELECT DISTINCT ?person ?personLabel ?birthDate ?deathDate ?occupationLabel ?countryLabel ?genderLabel WHERE {
  ?person wdt:P31 wd:Q5 .
  ?person wdt:P569 ?birthDate .
  OPTIONAL { ?person wdt:P570 ?deathDate . }
  OPTIONAL { ?person wdt:P106 ?occupation . }
  OPTIONAL { ?person wdt:P27 ?country . }
  OPTIONAL { ?person wdt:P21 ?gender . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "zh,en". }
}
ORDER BY ?person
LIMIT {limit}
OFFSET {offset}
"""

def fetch_batch(limit=1000, offset=0):
    query = QUERY_TPL.replace("{limit}", str(limit)).replace("{offset}", str(offset))
    _rl()
    try:
        resp = requests.get(WDQ, params={"format": "json", "query": query},
                           headers={"User-Agent": "GCalc/1.0"},
                           proxies=_px(), timeout=60)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"[wdq] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[wdq] Error: {e}")
    return None

def fetch_all(target=10000, batch_size=1000):
    collector = DataCollector()
    total = 0
    seen_qids = set()
    for batch_num in range(0, target, batch_size):
        offset = batch_num
        print(f"[wdq] Fetching batch offset={offset} limit={batch_size}...")
        data = fetch_batch(batch_size, offset)
        if not data:
            print("[wdq] Empty response, stopping")
            break
        results = data.get("results", {}).get("bindings", [])
        if not results:
            print("[wdq] No more results, stopping")
            break
        for row in results:
            qid = row.get("person", {}).get("value", "").split("/")[-1]
            if qid in seen_qids:
                continue
            seen_qids.add(qid)
            label = row.get("personLabel", {}).get("value", "")
            birth = parse_wd_date(row.get("birthDate", {}).get("value", ""))
            death = parse_wd_date(row.get("deathDate", {}).get("value", ""))
            if not birth:
                continue
            occupation = row.get("occupationLabel", {}).get("value", "")
            country = row.get("countryLabel", {}).get("value", "")
            gender = row.get("genderLabel", {}).get("value", "")
            gender_en = "male" if gender in ("male", "男") else "female" if gender in ("female", "女") else ""
            bazi_valid = 1500 <= birth["year"] <= 2026
            kw_tags = set()
            for kw in ["scientist", "writer", "artist", "philosopher",
                        "politician", "musician", "actor", "engineer",
                        "physicist", "chemist", "biologist", "mathematician",
                        "inventor", "explorer", "composer", "painter",
                        "poet", "novelist", "historian", "economist",
                        "astronomer", "physician", "psychologist"]:
                if kw.lower() in occupation.lower():
                    kw_tags.add(kw)
            combined_occ = " / ".join(sorted(kw_tags)) if kw_tags else occupation
            p = Person(
                name=label,
                birth_year=birth["year"],
                birth_month=birth["month"],
                birth_day=birth["day"],
                death_year=death["year"] if death else None,
                death_month=death["month"] if death else None,
                death_day=death["day"] if death else None,
                gender=gender_en,
                nationality=country,
                occupation=combined_occ,
                wiki_url=f"https://www.wikidata.org/wiki/{qid}",
                source="wikidata-10k",
                verified=False,
                birth_hour=12 if bazi_valid else None,
            )
            collector.add_person(p)
            total += 1
        print(f"[wdq] Batch done: {len(results)} results, {total} unique so far")
    out = os.path.join(DATA_DIR, "wikidata_10k.json")
    collector.export_json(out)
    print(f"[wdq] Total: {total} persons -> {out}")
    return collector

def merge_all():
    files = [
        os.path.join(DATA_DIR, "seed_data.json"),
        os.path.join(DATA_DIR, "twins_collected.json"),
        os.path.join(DATA_DIR, "wikidata_10k.json"),
    ]
    collector = DataCollector()
    for fp in files:
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            for pd in data.get("persons", []):
                try:
                    p = Person(**{k: v for k, v in pd.items()
                                if k in Person.__dataclass_fields__ and v is not None})
                    collector.add_person(p)
                except Exception as e:
                    pass
            for ed in data.get("events", []):
                try:
                    e = LifeEvent(**{k: v for k, v in ed.items()
                                   if k in LifeEvent.__dataclass_fields__ and v is not None})
                    collector.add_event(e)
                except Exception:
                    pass
            print(f"  Loaded {len(data.get('persons',[]))} persons from {os.path.basename(fp)}")
    out = os.path.join(DATA_DIR, "persons_master.json")
    collector.export_json(out)
    print(f"[merge] Master dataset: {collector.summary()}")
    return collector

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=10000, help="Target person count")
    parser.add_argument("--batch", type=int, default=500, help="Batch size")
    parser.add_argument("--merge", action="store_true", help="Merge all sources")
    args = parser.parse_args()
    if args.merge:
        merge_all()
    else:
        fetch_all(args.target, args.batch)
