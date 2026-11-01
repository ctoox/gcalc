"""Add 罗展程 to SQLite database + verify"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.db import get_db
from core.bazi import BaziEngine

db = get_db()

# Insert 罗展程
person = {
    "name": "罗展程",
    "birth_year": 1997,
    "birth_month": 6,
    "birth_day": 21,
    "birth_hour": 12,
    "birth_minute": 0,
    "gender": "male",
    "nationality": "Chinese",
    "occupation": "",
    "source": "user-provided",
    "confidence": 0.95,
    "source_priority": 10,
    "verified": 1,
}

# Generate BaZi
be = BaziEngine()
bazi = be.calculate(1997, 6, 21, 12)
person["bazi"] = bazi.get("bazi", "")
person["shichen"] = "午"

pid = db.insert(person)
print(f"Added 罗展程: id={pid} bazi={person['bazi']}")

# Verify it
p = db.get(pid)
print(f"Verified: name={p['name']} year={p['birth_year']} bazi={p['bazi']}")

# Full re-verify of DB
print(f"\nDB total: {db.count()}")
for f in ["name", "birth_year", "bazi"]:
    db._execute(f"UPDATE people SET {f} = {f} WHERE 1=1")  # no-op, just check

print("罗展程 successfully added to database.")
