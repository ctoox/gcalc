import requests, time
t1 = time.time()
resp = requests.get("https://dbpedia.org/sparql",
    params={"format": "json", "query": "SELECT ?person ?name ?birth WHERE { ?person a dbo:Person . ?person foaf:name ?name . ?person dbo:birthDate ?birth . } LIMIT 1 OFFSET 0"},
    headers={"User-Agent": "GCalc/1.0"}, timeout=30)
t2 = time.time()
print(f"HTTP {resp.status_code} in {t2-t1:.1f}s")
if resp.status_code == 200:
    d = resp.json()
    r = d["results"]["bindings"][0]
    print(f"Name: {r['name']['value']}")
    print(f"Birth: {r['birth']['value']}")
