import requests, json, time

def test_offset(offset):
    q = 'SELECT DISTINCT ?person ?name ?birth WHERE { ?person a dbo:Person . ?person foaf:name ?name . ?person dbo:birthDate ?birth . FILTER (lang(?name) = "en") } ORDER BY ?person LIMIT 1 OFFSET ' + str(offset)
    t1 = time.time()
    resp = requests.get("https://dbpedia.org/sparql",
                       params={"format": "json", "query": q},
                       headers={"User-Agent": "GCalc/1.0"}, timeout=60)
    t2 = time.time()
    print(f"offset={offset}: HTTP {resp.status_code} in {t2-t1:.1f}s")
    if resp.status_code == 200:
        d = resp.json()
        r = d["results"]["bindings"]
        if r:
            print(f"  {r[0].get('name',{}).get('value','?')} - {r[0].get('birth',{}).get('value','?')}")
        else:
            print("  (empty)")
    return resp.status_code

# Try offsets around where we're stuck
for off in [800, 801, 802, 900, 1000, 10000]:
    test_offset(off)
    time.sleep(2)
