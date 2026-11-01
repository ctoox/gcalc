import requests, json, time, socket

SOURCES = [
    ("Wikipedia EN API", "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Albert+Einstein&format=json"),
    ("Wikipedia ZH API", "https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch=%E6%9D%8E%E7%99%BD&format=json"),
    ("Wikidata SPARQL", "https://query.wikidata.org/sparql?format=json&query=SELECT+?person+?personLabel+WHERE+{+?person+wdt:P31+wd:Q5+}+LIMIT+3"),
    ("Wikidata Entity", "https://www.wikidata.org/wiki/Special:EntityData/Q937.json"),
    ("DBpedia", "https://dbpedia.org/data/Albert_Einstein.json"),
    ("OpenLibrary", "https://openlibrary.org/search.json?q=einstein&limit=1"),
    ("MusicBrainz", "https://musicbrainz.org/ws/2/artist/?query=beethoven&fmt=json"),
    ("GeoNames", "http://api.geonames.org/countryInfo?username=demo"),
]

def test(name, url, timeout=20):
    print(f"  Testing {name}...", end=" ")
    try:
        resp = requests.get(url, timeout=timeout,
                          headers={"User-Agent": "GCalc/1.0"})
        if resp.status_code == 200:
            print(f"OK ({len(resp.text)} bytes)")
            return True
        elif resp.status_code == 429:
            print("RATE LIMITED")
            return False
        else:
            print(f"HTTP {resp.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("TIMEOUT")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"CONNECTION ERROR")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

print("Testing global data source connectivity...\n")
results = {}
for name, url in SOURCES:
    results[name] = test(name, url)
    time.sleep(1)

print(f"\nSummary:")
ok = sum(1 for v in results.values() if v)
print(f"  Reachable: {ok}/{len(results)}")
for name, ok in results.items():
    print(f"  {'✓' if ok else '✗'} {name}")
