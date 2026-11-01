"""Integration test: Flask app HTTP endpoints"""
import sys, os, threading, time, json
from urllib.parse import quote
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import app

# Start Flask in a thread
def run_server():
    app.run(host="127.0.0.1", port=20009, debug=False, use_reloader=False)

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(3)

def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:20009{path}", timeout=10) as r:
        return json.loads(r.read())

def q(s):
    return quote(s, safe='')

def test():
    # 1. Person list
    data = get("/api/persons?per_page=3")
    assert data['total'] == 10164, f"total={data['total']}"
    assert len(data['persons']) == 3
    print(f"GET /api/persons: {data['total']} total, {len(data['persons'])} returned - PASS")

    # 2. FTS search
    data = get("/api/persons?q=Einstein")
    assert data['total'] == 1
    assert data['persons'][0]['name'] == 'Albert Einstein'
    print(f"GET /api/persons?q=Einstein: found {data['persons'][0]['name']} - PASS")

    # 3. Stats
    data = get("/api/persons/stats")
    assert data['total'] == 10164
    assert data['has_bazi'] == 10164
    print(f"GET /api/persons/stats: {data['total']} people, {data['db_size_mb']}MB - PASS")

    # 4. Get by ID
    data = get(f"/api/persons/{q('Nikola Tesla_1856')}")
    assert data['name'] == 'Nikola Tesla'
    print(f"GET /api/persons/Nikola Tesla_1856: {data['name']}, {data['birth_year']} - PASS")

    # 5. By BaZi
    data = get(f"/api/persons/bazi/{q('癸卯 戊辰 丙寅 戊子')}")
    print(f"GET /api/persons/bazi/...: {data['total']} sharing Einstein's BaZi - PASS")

    # 6. Random
    data = get("/api/persons/random?n=3")
    assert len(data['persons']) == 3
    print(f"GET /api/persons/random: {[p['name'] for p in data['persons']]} - PASS")

    # 7. Filter
    data = get("/api/persons?category=scientist&per_page=2")
    assert data['total'] == 3490
    print(f"GET /api/persons?category=scientist: {data['total']} scientists - PASS")

    print("\n=== ALL 7 HTTP TESTS PASSED ===")

test()
