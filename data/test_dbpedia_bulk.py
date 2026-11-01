import requests, json, time

def sparql_count():
    q = "SELECT COUNT(?person) WHERE { ?person a dbo:Person . ?person dbo:birthDate ?birth . }"
    r = requests.get("https://dbpedia.org/sparql", params={"format": "json", "query": q},
                    headers={"User-Agent": "GCalc/1.0"}, timeout=60)
    d = r.json()
    count = int(d["results"]["bindings"][0][".1"]["value"])
    return count

def sparql_sample(limit=10, offset=0):
    q = f"""
    SELECT ?person ?name ?birth ?death ?comment WHERE {{
      ?person a dbo:Person .
      ?person foaf:name ?name .
      ?person dbo:birthDate ?birth .
      OPTIONAL {{ ?person dbo:deathDate ?death . }}
      OPTIONAL {{ ?person rdfs:comment ?comment . FILTER (lang(?comment) = 'en') }}
    }}
    LIMIT {limit} OFFSET {offset}
    """
    r = requests.get("https://dbpedia.org/sparql", params={"format": "json", "query": q},
                    headers={"User-Agent": "GCalc/1.0"}, timeout=120)
    return r.json()

def fetch_with_occupation(limit=10, offset=0):
    q = f"""
    SELECT ?person ?name ?birth ?death ?occ ?nationality WHERE {{
      ?person a dbo:Person .
      ?person foaf:name ?name .
      ?person dbo:birthDate ?birth .
      OPTIONAL {{ ?person dbo:deathDate ?death . }}
      OPTIONAL {{ ?person dbo:occupation ?occ . }}
      OPTIONAL {{ ?person dbo:nationality ?nationality . }}
      FILTER (lang(?name) = 'en')
    }}
    LIMIT {limit} OFFSET {offset}
    """
    r = requests.get("https://dbpedia.org/sparql", params={"format": "json", "query": q},
                    headers={"User-Agent": "GCalc/1.0"}, timeout=120)
    return r.json()

print("=== DBpedia Bulk Test ===")

# Count
print("\nCounting total persons...")
try:
    total = sparql_count()
    print(f"Total persons with birth dates: {total:,}")
except Exception as e:
    print(f"Count failed: {e}")
    total = 0

# Sample with occupations
print("\nSampling persons with occupations...")
try:
    data = fetch_with_occupation(10, 0)
    results = data["results"]["bindings"]
    print(f"Got {len(results)} results")
    for r in results:
        name = r.get("name", {}).get("value", "?")
        birth = r.get("birth", {}).get("value", "?")
        occ = r.get("occ", {}).get("value", "?")
        nat = r.get("nationality", {}).get("value", "?")
        print(f"  {name:40s} | {birth:15s} | {occ[:30]:30s} | {nat[:20]}")
except Exception as e:
    print(f"Sample failed: {e}")

# Test pagination - can we get 1000 at once?
print("\nTesting bulk fetch (1000 rows)...")
try:
    big = fetch_with_occupation(1000, 0)
    print(f"Got {len(big['results']['bindings'])} rows in one query")
    # Count unique occupations
    occs = set()
    for r in big["results"]["bindings"]:
        if r.get("occ"):
            occs.add(r["occ"]["value"])
    print(f"Unique occupations in sample: {len(occs)}")
except Exception as e:
    print(f"Bulk fetch failed: {e}")
