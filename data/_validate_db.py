"""Full data validation on SQLite database. 10164 people."""
import sys, os, json, re
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.db import get_db

db = get_db()
conn = db._connect()
cur = conn.cursor()

errors = []
warnings = []

# 1. Row count
cur.execute("SELECT COUNT(*) FROM people")
total = cur.fetchone()[0]
print(f"Total: {total}")
if total != 10164:
    errors.append(f"Expected 10164, got {total}")

# 2. Fields check
cur.execute("SELECT * FROM people LIMIT 1")
columns = [d[0] for d in cur.description]
print(f"Columns ({len(columns)}): {columns}")
expected = ["id", "name", "birth_year", "birth_month", "birth_day", "birth_hour",
            "birth_minute", "death_year", "death_month", "death_day", "gender",
            "nationality", "occupation", "category", "source", "bazi", "shichen",
            "wiki_url", "verified", "twin_group_id", "birth_order", "birth_city",
            "birth_country", "family_rank", "family_wealth", "confidence",
            "source_priority", "quality_tags", "environment_tags", "relations",
            "death_cause", "created_at"]
for e in expected:
    if e not in columns:
        errors.append(f"Missing column: {e}")

# 3. Name check
cur.execute("SELECT COUNT(*) FROM people WHERE name IS NULL OR name = ''")
empty_names = cur.fetchone()[0]
if empty_names:
    errors.append(f"Empty names: {empty_names}")

cur.execute("SELECT LENGTH(name) FROM people ORDER BY LENGTH(name) DESC LIMIT 1")
max_name_len = cur.fetchone()[0]
print(f"Max name length: {max_name_len}")

# 4. Birth year range
cur.execute("SELECT MIN(birth_year), MAX(birth_year) FROM people")
min_y, max_y = cur.fetchone()
print(f"Birth years: {min_y} ~ {max_y}")
if max_y > 2026:
    errors.append(f"Future birth year: {max_y}")

# 5. Death year sanity
cur.execute("SELECT COUNT(*) FROM people WHERE death_year IS NOT NULL AND death_year < birth_year AND birth_year > 0")
bad_death = cur.fetchone()[0]
if bad_death:
    errors.append(f"Death before birth: {bad_death}")

# 6. Lifespan
cur.execute("""SELECT death_year - birth_year as lifespan FROM people
               WHERE death_year IS NOT NULL AND birth_year IS NOT NULL AND birth_year > 0""")
lifespans = [r[0] for r in cur.fetchall()]
too_old = sum(1 for l in lifespans if l > 120)
if too_old:
    warnings.append(f"Lifespan > 120: {too_old}")
print(f"Lifespan: min={min(lifespans)} max={max(lifespans)} avg={sum(lifespans)/len(lifespans):.0f}")

# 7. Month/day range
cur.execute("SELECT COUNT(*) FROM people WHERE birth_month NOT BETWEEN 1 AND 12")
bad_month = cur.fetchone()[0]
if bad_month:
    errors.append(f"Bad birth_month: {bad_month}")
cur.execute("SELECT COUNT(*) FROM people WHERE birth_day NOT BETWEEN 1 AND 31")
bad_day = cur.fetchone()[0]
if bad_day:
    errors.append(f"Bad birth_day: {bad_day}")

# 8. BaZi format (4 pairs of Chinese chars separated by spaces)
bazi_pat = re.compile(r'^[\u4e00-\u9fff]{2} [\u4e00-\u9fff]{2} [\u4e00-\u9fff]{2} [\u4e00-\u9fff]{2}$')
cur.execute("SELECT bazi FROM people")
bad_bazi = sum(1 for r in cur.fetchall() if not bazi_pat.match(r[0] or ""))
if bad_bazi:
    errors.append(f"Bad BaZi format: {bad_bazi}")
cur.execute("SELECT COUNT(DISTINCT bazi) FROM people")
unique_bazi = cur.fetchone()[0]
print(f"Unique BaZi: {unique_bazi}/{total}")

# 9. Gender
cur.execute("SELECT gender, COUNT(*) FROM people WHERE gender != '' GROUP BY gender")
genders = dict(cur.fetchall())
print(f"Gender: {genders}")
cur.execute("SELECT COUNT(*) FROM people WHERE gender NOT IN ('male', 'female', '')")
bad_gender = cur.fetchone()[0]
if bad_gender:
    errors.append(f"Invalid gender: {bad_gender}")

# 10. Nationalities
cur.execute("SELECT COUNT(DISTINCT nationality) FROM people WHERE nationality != ''")
nats = cur.fetchone()[0]
print(f"Nationalities: {nats}")

# 11. Duplicate IDs
cur.execute("SELECT id, COUNT(*) as cnt FROM people GROUP BY id HAVING cnt > 1")
dups = cur.fetchall()
if dups:
    warnings.append(f"Duplicate IDs: {len(dups)} groups")
    for d in dups[:5]:
        warnings.append(f"  {d['id']}: {d['cnt']}")

# 12. Nulls in critical fields
for f in ["name", "birth_year", "birth_month", "birth_day", "bazi"]:
    cur.execute(f"SELECT COUNT(*) FROM people WHERE {f} IS NULL OR {f} = ''")
    n = cur.fetchone()[0]
    if n:
        errors.append(f"Null/empty {f}: {n}")

# 13. Source distribution
cur.execute("SELECT source, COUNT(*) FROM people GROUP BY source")
sources = dict(cur.fetchall())
print(f"Sources: {sources}")

# 14. Confidence
cur.execute("SELECT MIN(confidence), AVG(confidence), MAX(confidence) FROM people")
min_c, avg_c, max_c = cur.fetchone()
print(f"Confidence: {min_c:.2f} ~ {max_c:.2f} (avg {avg_c:.2f})")

# 15. DB size
db_size = os.path.getsize(db.db_path) / 1024 / 1024
print(f"DB file: {db_size:.1f}MB")

# Summary
print(f"\n{'='*50}")
print(f"ERRORS: {len(errors)}")
for e in errors:
    print(f"  ✗ {e}")
print(f"WARNINGS: {len(warnings)}")
for w in warnings:
    print(f"  ⚠ {w}")
if not errors:
    print("✓ ALL CHECKS PASSED")

conn.close()
