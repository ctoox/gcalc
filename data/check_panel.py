import requests

r = requests.get("http://127.0.0.1:20001/api/persons?per_page=5", timeout=5)
d = r.json()
print(f"Total persons: {d['total']}")
print(f"Page: {d['page']}/{d['pages']}")
for i, p in enumerate(d["persons"]):
    print(f"  {i+1}. {p['name']} ({p.get('birth_year','?')}) - {str(p.get('occupation','?'))[:30]}")

# Also test the web page
r2 = requests.get("http://127.0.0.1:20001/persons", timeout=5)
print(f"\nPerson panel HTML: {len(r2.text)} bytes, HTTP {r2.status_code}")
if "Global Person Database" in r2.text:
    print("Panel title OK")
