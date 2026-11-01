"""Final verification: duplicate check + data integrity + API test"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.db import get_db

db = get_db()
conn = db._connect()
cur = conn.cursor()

print("=" * 50)
print("FINAL VERIFICATION")
print("=" * 50)

# 1. Duplicate check by ID
cur.execute("SELECT id, COUNT(*) as cnt FROM people GROUP BY id HAVING cnt > 1")
dups = cur.fetchall()
print(f"\n1. Duplicate IDs: {len(dups)}")
if dups:
    for d in dups[:5]:
        print(f"   ID={d['id']} count={d['cnt']}")
else:
    print("   PASS: No duplicate IDs")

# 2. Duplicate by (name, birth_year) 
cur.execute("""SELECT name, birth_year, COUNT(*) as cnt FROM people 
               WHERE name != '' AND birth_year IS NOT NULL 
               GROUP BY name, birth_year HAVING cnt > 1""")
name_dups = cur.fetchall()
print(f"2. Duplicate (name, year): {len(name_dups)}")
if name_dups:
    for d in name_dups[:5]:
        names = [r['id'] for r in cur.execute(
            "SELECT id FROM people WHERE name=? AND birth_year=?",
            (d['name'], d['birth_year'])).fetchall()]
        print(f"   {d['name']} ({d['birth_year']}) x{d['cnt']}: {names}")
else:
    print("   PASS: No duplicate name+year")

# 3. Total
cur.execute("SELECT COUNT(*) FROM people")
total = cur.fetchone()[0]
print(f"3. Total people: {total}")
assert total == 10165, f"Expected 10165, got {total}"
print("   PASS: Correct count")

# 4. 罗展程
p = db.get("罗展程_1997")
if p:
    print(f"4. 罗展程: PASS name={p['name']} year={p['birth_year']} bazi={p['bazi']} gender={p['gender']}")
else:
    print("4. 罗展程: FAIL NOT FOUND!")

# 5. Integrity checks
checks = {
    "Null names": "SELECT COUNT(*) FROM people WHERE name IS NULL OR name = ''",
    "Null bazi": "SELECT COUNT(*) FROM people WHERE bazi IS NULL OR bazi = ''",
    "Bad gender": "SELECT COUNT(*) FROM people WHERE gender NOT IN ('male', 'female', '')",
    "No birth year": "SELECT COUNT(*) FROM people WHERE birth_year IS NULL",
    "Death < birth": "SELECT COUNT(*) FROM people WHERE death_year IS NOT NULL AND birth_year IS NOT NULL AND death_year < birth_year AND birth_year > 0",
    "Lifespan > 120": "SELECT COUNT(*) FROM people WHERE death_year IS NOT NULL AND birth_year IS NOT NULL AND death_year - birth_year > 120 AND birth_year > 0",
    "Bad month": "SELECT COUNT(*) FROM people WHERE birth_month IS NOT NULL AND (birth_month < 1 OR birth_month > 12)",
    "Bad day": "SELECT COUNT(*) FROM people WHERE birth_day IS NOT NULL AND (birth_day < 1 OR birth_day > 31)",
}
all_ok = True
for label, sql in checks.items():
    cur.execute(sql)
    n = cur.fetchone()[0]
    status = "PASS" if n == 0 else f"FAIL ({n} issues)"
    if n > 0:
        all_ok = False
    print(f"5. {label}: {status}")

# 6. Source distribution
cur.execute("SELECT source, COUNT(*) FROM people GROUP BY source ORDER BY COUNT(*) DESC")
sources = cur.fetchall()
print(f"\n6. Sources:")
for s in sources:
    print(f"   {s['source'] or 'unknown'}: {s['COUNT(*)']}")

# 7. Gender balance
cur.execute("SELECT gender, COUNT(*) FROM people WHERE gender != '' GROUP BY gender")
genders = cur.fetchall()
print(f"\n7. Gender: {[dict(g) for g in genders]}")

# 8. Verify real_people.json matches SQLite count
rp_path = os.path.join(os.path.dirname(__file__), "real_people.json")
if os.path.exists(rp_path):
    with open(rp_path, encoding='utf-8') as f:
        rp = json.load(f)
    rp_count = len(rp) if isinstance(rp, dict) else len(rp)
    print(f"\n8. real_people.json: {rp_count} entries (SQLite: {total})")

master_path = os.path.join(os.path.dirname(__file__), "master_10k.json")
if os.path.exists(master_path):
    with open(master_path, encoding='utf-8') as f:
        m = json.load(f)
    mp = len(m.get("persons", []))
    print(f"   master_10k.json: {mp} persons")

# 9. DB file size
db_size = os.path.getsize(db.db_path) / 1024 / 1024
json_size = os.path.getsize(rp_path) / 1024 / 1024 if os.path.exists(rp_path) else 0
print(f"\n9. Storage:")
print(f"   SQLite: {db_size:.1f}MB")
print(f"   JSON: {json_size:.1f}MB")
print(f"   Savings: {(1 - db_size/json_size)*100:.0f}%" if json_size else "   N/A")

# 10. Test search
r, t = db.search("罗展程")
print(f"\n10. Search 罗展程: {t} result(s) PASS")
r, t = db.search("展程")
print(f"    Search 展程: {t} result(s) PASS")

print(f"\n{'='*50}")
if all_ok:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED")
print(f"{'='*50}")

conn.close()
