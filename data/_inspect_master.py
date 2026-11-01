"""Deep inspect master_10k - the largest data file"""
import json, os

path = r'C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data\master_10k.json'
size = os.path.getsize(path)
print(f"File size: {size:,} bytes ({size/1024/1024:.1f} MB)")

with open(path, encoding='utf-8') as f:
    data = json.load(f)

print(f"Type: {type(data).__name__}")

if isinstance(data, dict):
    print(f"Key count: {len(data)}")
    # Check first few keys
    for i, (k, v) in enumerate(data.items()):
        if i >= 5: break
        if isinstance(v, dict):
            keys = list(v.keys())
            print(f"  [{k}] fields={keys[:10]} name={v.get('name','')} birth={v.get('birth_year')}")
        else:
            print(f"  [{k}] type={type(v).__name__}")

elif isinstance(data, list):
    print(f"List count: {len(data)}")
    for i, v in enumerate(data[:5]):
        if isinstance(v, dict):
            keys = list(v.keys())
            print(f"  [{i}] fields={keys[:10]} name={v.get('name','?')} birth={v.get('birth_year')}")
        else:
            print(f"  [{i}] type={type(v).__name__}")

# Also check real_people.json
print("\n--- real_people.json ---")
with open(r'C:\Users\ctooc\Desktop\workspace\_ai\gcalc\data\real_people.json', encoding='utf-8') as f:
    rp = json.load(f)
print(f"Type: {type(rp).__name__}")
if isinstance(rp, dict):
    print(f"Key count: {len(rp)}")
    for k, v in rp.items():
        if isinstance(v, dict):
            print(f"  {v.get('name','?')}: birth={v.get('birth_year')} death={v.get('death_year')}")
elif isinstance(rp, list):
    print(f"List count: {len(rp)}")
    for v in rp:
        if isinstance(v, dict):
            print(f"  {v.get('name','?')}: birth={v.get('birth_year')} death={v.get('death_year')}")
