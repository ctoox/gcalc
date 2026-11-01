import os, json, requests

real_file = os.path.join(os.path.dirname(__file__), "real_people.json")
state_file = os.path.join(os.path.dirname(__file__), "slow_state.json")

print(f"real_people.json exists: {os.path.exists(real_file)}")
print(f"slow_state.json exists: {os.path.exists(state_file)}")

if os.path.exists(state_file):
    with open(state_file) as f:
        s = json.load(f)
    print(f"State: {json.dumps(s, indent=2)}")

if os.path.exists(real_file):
    with open(real_file, encoding="utf-8") as f:
        d = json.load(f)
    print(f"Persons in real_people.json: {d['summary']['total_persons']}")

try:
    r = requests.get("http://127.0.0.1:20001/api/persons/stats", timeout=5)
    print(f"\nWeb API stats: {r.text[:300]}")
except Exception as e:
    print(f"\nWeb API error: {e}")
