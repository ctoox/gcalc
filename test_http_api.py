"""Start Flask server in background, test HTTP API endpoints"""
import subprocess, time, requests, sys, os, signal

SERVE = os.path.join(os.path.dirname(__file__), "..", "app.py")

# Start server
proc = subprocess.Popen(
    [sys.executable, SERVE],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
time.sleep(4)  # Wait for startup

try:
    base = "http://127.0.0.1:20002"

    # Test persons list
    r = requests.get(f"{base}/api/persons?per_page=3", timeout=10)
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    print(f"GET /api/persons?per_page=3 -> {data['total']} total, {len(data['persons'])} returned")
    assert data['total'] == 10164
    print("  PASS")

    # Test search
    r = requests.get(f"{base}/api/persons?q=Einstein&per_page=5", timeout=10)
    assert r.status_code == 200
    data = r.json()
    print(f"GET /api/persons?q=Einstein -> {data['total']} result(s)")
    assert data['total'] == 1
    assert data['persons'][0]['name'] == 'Albert Einstein'
    print("  PASS")

    # Test stats
    r = requests.get(f"{base}/api/persons/stats", timeout=10)
    assert r.status_code == 200
    s = r.json()
    print(f"GET /api/persons/stats -> total={s['total']}, nats={s['nationalities']}, occs={s['occupations']}")
    assert s['total'] == 10164
    print("  PASS")

    # Test random
    r = requests.get(f"{base}/api/persons/random?n=3", timeout=10)
    assert r.status_code == 200
    data = r.json()
    print(f"GET /api/persons/random?n=3 -> {len(data['persons'])} random people")
    assert len(data['persons']) == 3
    print("  PASS")

    # Test get by BaZi
    r = requests.get(f"{base}/api/persons/bazi/癸卯 戊辰 丙寅 戊子", timeout=10)
    assert r.status_code == 200
    print(f"GET /api/persons/bazi/... -> {len(r.json()['persons'])} result(s)")
    print("  PASS")

    # Test get by ID
    r = requests.get(f"{base}/api/persons/Albert Einstein_1879", timeout=10)
    assert r.status_code == 200
    p = r.json()
    print(f"GET /api/persons/Albert Einstein_1879 -> {p['name']}, {p['birth_year']}")
    assert p['name'] == 'Albert Einstein'
    print("  PASS")

    print("\n=== ALL HTTP TESTS PASSED ===")

finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
