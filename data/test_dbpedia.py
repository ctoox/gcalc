import requests, json

url = "https://dbpedia.org/sparql"
query = "SELECT ?person ?name ?birth WHERE { ?person a dbo:Person . ?person foaf:name ?name . ?person dbo:birthDate ?birth . } LIMIT 5"
resp = requests.get(url, params={"format": "json", "query": query},
                   headers={"User-Agent": "GCalc/1.0"}, timeout=30)
print(f"DBpedia SPARQL: HTTP {resp.status_code}")
d = resp.json()
for r in d["results"]["bindings"]:
    name = r.get("name", {}).get("value", "?")
    birth = r.get("birth", {}).get("value", "?")
    print(f"  {name} - {birth}")

# Test resource API
print("\nDBpedia Resource API:")
resp2 = requests.get("https://dbpedia.org/data/Albert_Einstein.json",
                     headers={"User-Agent": "GCalc/1.0"}, timeout=30)
print(f"  HTTP {resp2.status_code}")
d2 = resp2.json()
uri = "http://dbpedia.org/resource/Albert_Einstein"
if uri in d2:
    data = d2[uri]
    print(f"  Fields: {list(data.keys())[:10]}")
    birth = data.get("http://dbpedia.org/ontology/birthDate", [{}])
    if birth:
        print(f"  Birth: {birth[0].get('value', '?')}")
    death = data.get("http://dbpedia.org/ontology/deathDate", [{}])
    if death:
        print(f"  Death: {death[0].get('value', '?')}")
    occ = data.get("http://dbpedia.org/ontology/occupation", [{}])
    if occ:
        print(f"  Occupation: {occ[0].get('value', '?')}")
