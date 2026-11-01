"""SQLite database layer for gcalc.
Single-file, lightweight, FTS5 full-text search, indexed for fast queries.
Handles 10K+ → millions of people records efficiently."""
import sqlite3, os, json, time
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gcalc.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS people (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    birth_year  INTEGER,
    birth_month INTEGER,
    birth_day   INTEGER,
    birth_hour  INTEGER,
    birth_minute INTEGER DEFAULT 0,
    death_year  INTEGER,
    death_month INTEGER,
    death_day   INTEGER,
    gender      TEXT,
    nationality TEXT,
    occupation  TEXT,
    category    TEXT,
    source      TEXT,
    bazi        TEXT,
    shichen     TEXT,
    wiki_url    TEXT,
    verified    INTEGER DEFAULT 0,
    twin_group_id TEXT,
    birth_order INTEGER,
    birth_city  TEXT,
    birth_country TEXT,
    family_rank TEXT,
    family_wealth REAL,
    confidence  REAL DEFAULT 0.7,
    source_priority INTEGER DEFAULT 5,
    quality_tags   TEXT DEFAULT '[]',
    environment_tags TEXT DEFAULT '[]',
    relations    TEXT DEFAULT '{}',
    death_cause  TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_people_birth_year ON people(birth_year);
CREATE INDEX IF NOT EXISTS idx_people_death_year ON people(death_year);
CREATE INDEX IF NOT EXISTS idx_people_nationality ON people(nationality);
CREATE INDEX IF NOT EXISTS idx_people_occupation ON people(occupation);
CREATE INDEX IF NOT EXISTS idx_people_bazi ON people(bazi);
CREATE INDEX IF NOT EXISTS idx_people_gender ON people(gender);
CREATE INDEX IF NOT EXISTS idx_people_source ON people(source);
CREATE INDEX IF NOT EXISTS idx_people_priority ON people(source_priority);
CREATE INDEX IF NOT EXISTS idx_people_verified ON people(verified);
CREATE INDEX IF NOT EXISTS idx_people_twin ON people(twin_group_id);

CREATE VIRTUAL TABLE IF NOT EXISTS people_fts USING fts5(
    name, occupation, nationality, bazi, shichen, birth_city,
    content='people',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS people_fts_insert AFTER INSERT ON people BEGIN
    INSERT INTO people_fts(rowid, name, occupation, nationality, bazi, shichen, birth_city)
    VALUES (new.rowid, new.name, new.occupation, new.nationality, new.bazi, new.shichen, new.birth_city);
END;

CREATE TRIGGER IF NOT EXISTS people_fts_delete AFTER DELETE ON people BEGIN
    INSERT INTO people_fts(people_fts, rowid, name, occupation, nationality, bazi, shichen, birth_city)
    VALUES ('delete', old.rowid, old.name, old.occupation, old.nationality, old.bazi, old.shichen, old.birth_city);
END;

CREATE TRIGGER IF NOT EXISTS people_fts_update AFTER UPDATE ON people BEGIN
    INSERT INTO people_fts(people_fts, rowid, name, occupation, nationality, bazi, shichen, birth_city)
    VALUES ('delete', old.rowid, old.name, old.occupation, old.nationality, old.bazi, old.shichen, old.birth_city);
    INSERT INTO people_fts(rowid, name, occupation, nationality, bazi, shichen, birth_city)
    VALUES (new.rowid, new.name, new.occupation, new.nationality, new.bazi, new.shichen, new.birth_city);
END;

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id   TEXT REFERENCES people(id),
    year        INTEGER,
    month       INTEGER,
    day         INTEGER,
    event_type  TEXT,
    description TEXT,
    significance INTEGER DEFAULT 5,
    source      TEXT,
    UNIQUE(person_id, year, month, day, event_type)
);

CREATE INDEX IF NOT EXISTS idx_events_person ON events(person_id);
CREATE INDEX IF NOT EXISTS idx_events_year ON events(year);

CREATE TABLE IF NOT EXISTS twin_groups (
    group_id   TEXT PRIMARY KEY,
    person_ids TEXT NOT NULL,
    count      INTEGER DEFAULT 2,
    study_type TEXT DEFAULT 'synthetic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', '1');
INSERT OR IGNORE INTO meta(key, value) VALUES ('total_people', '0');
INSERT OR IGNORE INTO meta(key, value) VALUES ('last_migration', '');
"""


class PeopleDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_schema()

    # ── connection ──

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self):
        conn = self._connect()
        try:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
        finally:
            conn.close()

    # ── internal helpers ──

    def _row_to_dict(self, row):
        if row is None:
            return None
        d = dict(row)
        # Parse JSON fields
        for f in ("quality_tags", "environment_tags", "relations"):
            if f in d and isinstance(d[f], str):
                try:
                    d[f] = json.loads(d[f])
                except (json.JSONDecodeError, TypeError):
                    d[f] = [] if f != "relations" else {}
        return d

    def _rows_to_list(self, rows):
        return [self._row_to_dict(r) for r in rows]

    def _execute(self, sql, params=None):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params or [])
            conn.commit()
            return cur
        finally:
            conn.close()

    def _fetchone(self, sql, params=None):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params or [])
            return cur.fetchone()
        finally:
            conn.close()

    def _fetchall(self, sql, params=None):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params or [])
            return cur.fetchall()
        finally:
            conn.close()

    # ── CRUD ──

    def get(self, person_id):
        row = self._fetchone("SELECT rowid, * FROM people WHERE id = ?", (person_id,))
        return self._row_to_dict(row)

    def get_by_rowid(self, rowid):
        row = self._fetchone("SELECT rowid, * FROM people WHERE rowid = ?", (rowid,))
        return self._row_to_dict(row)

    def get_all(self, limit=100, offset=0):
        rows = self._fetchall(
            "SELECT rowid, * FROM people ORDER BY source_priority DESC, name LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return self._rows_to_list(rows), self.count()

    def search(self, query, limit=50, offset=0):
        """FTS5 full-text search with LIKE fallback for CJK partial names."""
        if not query or not query.strip():
            return self.get_all(limit, offset)
        q = query.strip()
        # For CJK text, split each character into individual match terms
        # Unicode61 tokenizer treats each CJK char as a separate token
        has_cjk = any('\u4e00' <= c <= '\u9fff' or '\u3000' <= c <= '\u303f' for c in q)
        if has_cjk:
            fts_terms = " AND ".join(c for c in q if c.strip() and ('\u4e00' <= c <= '\u9fff'))
        else:
            fts_terms = " OR ".join(q.split())

        # Try FTS5 first
        sql = """SELECT p.rowid, * FROM people p
                 JOIN people_fts f ON p.rowid = f.rowid
                 WHERE people_fts MATCH ?
                 ORDER BY rank
                 LIMIT ? OFFSET ?"""
        try:
            fts_rows = self._fetchall(sql, (fts_terms, limit, offset))
            if fts_rows:
                count_sql = """SELECT COUNT(*) as cnt FROM people p
                               JOIN people_fts f ON p.rowid = f.rowid
                               WHERE people_fts MATCH ?"""
                total_row = self._fetchone(count_sql, (fts_terms,))
                total = total_row["cnt"] if total_row else 0
                return self._rows_to_list(fts_rows), total
        except Exception:
            pass

        # Fallback: LIKE search (handles CJK partial names better)
        like = f"%{q}%"
        rows = self._fetchall(
            """SELECT rowid, * FROM people
               WHERE name LIKE ? OR occupation LIKE ? OR nationality LIKE ? OR bazi LIKE ?
               ORDER BY source_priority DESC, name
               LIMIT ? OFFSET ?""",
            (like, like, like, like, limit, offset),
        )
        total_row = self._fetchone(
            """SELECT COUNT(*) as cnt FROM people
               WHERE name LIKE ? OR occupation LIKE ? OR nationality LIKE ? OR bazi LIKE ?""",
            (like, like, like, like),
        )
        total = total_row["cnt"] if total_row else 0
        return self._rows_to_list(rows), total

    def filter(self, nationality=None, occupation=None, category=None,
               year_from=None, year_to=None, gender=None, source=None,
               verified=None, has_bazi=None,
               page=1, per_page=50, sort_by="name"):
        """Advanced filtering with pagination."""
        conditions = []
        params = []
        if nationality:
            conditions.append("nationality LIKE ?")
            params.append(f"%{nationality}%")
        if occupation:
            conditions.append("occupation LIKE ?")
            params.append(f"%{occupation}%")
        if category:
            conditions.append("category = ?")
            params.append(category)
        if year_from is not None:
            conditions.append("birth_year >= ?")
            params.append(year_from)
        if year_to is not None:
            conditions.append("birth_year <= ?")
            params.append(year_to)
        if gender:
            conditions.append("gender = ?")
            params.append(gender)
        if source:
            conditions.append("source = ?")
            params.append(source)
        if verified is not None:
            conditions.append("verified = ?")
            params.append(1 if verified else 0)
        if has_bazi:
            conditions.append("bazi IS NOT NULL AND bazi != ''")

        where = " AND ".join(conditions) if conditions else "1=1"

        sort_map = {
            "name": "name",
            "year": "birth_year",
            "year_desc": "birth_year DESC",
            "priority": "source_priority DESC",
            "confidence": "confidence DESC",
            "death": "death_year",
        }
        order = sort_map.get(sort_by, "name")
        if sort_by == "name":
            order += " COLLATE NOCASE"

        offset = (page - 1) * per_page
        rows = self._fetchall(
            f"SELECT rowid, * FROM people WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
            params + [per_page, offset],
        )
        total_row = self._fetchone(
            f"SELECT COUNT(*) as cnt FROM people WHERE {where}", params
        )
        total = total_row["cnt"] if total_row else 0
        return self._rows_to_list(rows), total

    def insert(self, person):
        """Insert or replace a person record."""
        d = {}
        for f, default in self.DEFAULTS.items():
            v = person.get(f)
            if v is None:
                v = person.get(f, default)
            d[f] = v
        for f in ("quality_tags", "environment_tags"):
            if f in d and not isinstance(d[f], str):
                d[f] = json.dumps(d[f], ensure_ascii=False)
        if "relations" in d and not isinstance(d["relations"], str):
            d["relations"] = json.dumps(d["relations"], ensure_ascii=False)
        if not d.get("id"):
            d["id"] = f"{d.get('name', '?')}_{d.get('birth_year', 0)}"
        fields = list(self.DEFAULTS.keys())
        placeholders = ", ".join(f":{f}" for f in fields)
        names = ", ".join(fields)
        sql = f"INSERT OR REPLACE INTO people ({names}) VALUES ({placeholders})"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, d)
            conn.commit()
            return d.get("id", "")
        finally:
            conn.close()

    DEFAULTS = {
        "id": "", "name": "", "birth_year": None, "birth_month": None, "birth_day": None,
        "birth_hour": None, "birth_minute": 0,
        "death_year": None, "death_month": None, "death_day": None,
        "gender": "", "nationality": "", "occupation": "", "category": "", "source": "",
        "bazi": "", "shichen": "", "wiki_url": "", "verified": 0,
        "twin_group_id": "", "birth_order": None,
        "birth_city": "", "birth_country": "",
        "family_rank": "", "family_wealth": None,
        "confidence": 0.7, "source_priority": 5,
        "quality_tags": "[]", "environment_tags": "[]", "relations": "{}",
        "death_cause": "",
    }

    def bulk_insert(self, people, batch_size=500):
        """Insert many people efficiently."""
        conn = self._connect()
        count = 0
        try:
            cur = conn.cursor()
            fields = list(self.DEFAULTS.keys())
            placeholders = ", ".join(f":{f}" for f in fields)
            names = ", ".join(fields)
            sql = f"INSERT OR REPLACE INTO people ({names}) VALUES ({placeholders})"
            batch = []
            for p in people:
                d = {}
                for f, default in self.DEFAULTS.items():
                    v = p.get(f)
                    if v is None:
                        v = p.get(f, default)
                    d[f] = v
                for f in ("quality_tags", "environment_tags"):
                    if f in d and not isinstance(d[f], str):
                        d[f] = json.dumps(d[f], ensure_ascii=False)
                if "relations" in d and not isinstance(d["relations"], str):
                    d["relations"] = json.dumps(d["relations"], ensure_ascii=False)
                if not d.get("id"):
                    d["id"] = f"{d.get('name', '?')}_{d.get('birth_year', 0)}"
                batch.append(d)
                count += 1
                if len(batch) >= batch_size:
                    cur.executemany(sql, batch)
                    conn.commit()
                    batch = []
            if batch:
                cur.executemany(sql, batch)
                conn.commit()
            cur.execute("UPDATE meta SET value = ? WHERE key = 'total_people'", (str(count),))
            conn.commit()
        finally:
            conn.close()
        return count

    def delete(self, person_id):
        self._execute("DELETE FROM people WHERE id = ?", (person_id,))

    def count(self):
        row = self._fetchone("SELECT COUNT(*) as cnt FROM people")
        return row["cnt"] if row else 0

    # ── Migration ──

    def import_from_json(self, json_path, source_tag=None):
        """Import from any JSON file (list or dict of people)."""
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Dict of {name_year: person} or {key: {persons: [...], ...}}
            if "persons" in data:
                people = data["persons"]
            else:
                people = list(data.values())
        elif isinstance(data, list):
            people = data
        else:
            raise ValueError(f"Unexpected JSON type: {type(data)}")

        if source_tag:
            for p in people:
                if isinstance(p, dict) and "source" not in p:
                    p["source"] = source_tag

        count = self.bulk_insert(people)
        # Also import events if present
        if isinstance(data, dict) and "events" in data:
            self._import_events(data["events"])
        if isinstance(data, dict) and "twin_groups" in data:
            self._import_twin_groups(data["twin_groups"])

        self._execute(
            "UPDATE meta SET value = ? WHERE key = 'last_migration'",
            (f"{json_path} -> {count} people @ {time.strftime('%Y-%m-%d %H:%M:%S')}",),
        )
        return count

    def _import_events(self, events):
        if not events:
            return
        conn = self._connect()
        try:
            cur = conn.cursor()
            for ev in events:
                cur.execute(
                    """INSERT OR IGNORE INTO events
                       (person_id, year, month, day, event_type, description, significance, source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ev.get("person_id", ""),
                        ev.get("year"),
                        ev.get("month", 1),
                        ev.get("day", 1),
                        ev.get("event_type", ""),
                        ev.get("description", ""),
                        ev.get("significance", 5),
                        ev.get("source", ""),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def _import_twin_groups(self, twin_groups):
        if not twin_groups:
            return
        conn = self._connect()
        try:
            cur = conn.cursor()
            for gid, members in twin_groups.items():
                if isinstance(members, list):
                    ids = [m.get("id", "") if isinstance(m, dict) else str(m) for m in members]
                elif isinstance(members, dict):
                    ids = [members.get("id", "")]
                else:
                    ids = [str(members)]
                cur.execute(
                    "INSERT OR REPLACE INTO twin_groups(group_id, person_ids, count) VALUES (?, ?, ?)",
                    (gid, json.dumps(ids, ensure_ascii=False), len(ids)),
                )
            conn.commit()
        finally:
            conn.close()

    def export_to_json(self, json_path, limit=None):
        """Export people to JSON file."""
        if limit:
            rows = self._fetchall(
                "SELECT * FROM people ORDER BY source_priority DESC, name LIMIT ?", (limit,)
            )
        else:
            rows = self._fetchall("SELECT * FROM people ORDER BY source_priority DESC, name")
        people = self._rows_to_list(rows)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(people, f, ensure_ascii=False, indent=2)
        return len(people)

    # ── Stats ──

    def stats(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as total FROM people")
            total = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(DISTINCT nationality) FROM people WHERE nationality != ''")
            nats = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT occupation) FROM people WHERE occupation != ''")
            occs = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT category) FROM people WHERE category != ''")
            cats = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM people WHERE verified = 1")
            verified = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM people WHERE bazi IS NOT NULL AND bazi != ''")
            has_bazi = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM people WHERE death_year IS NOT NULL")
            has_death = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT twin_group_id) FROM people WHERE twin_group_id IS NOT NULL AND twin_group_id != ''")
            twin_groups = cur.fetchone()[0]

            cur.execute("""SELECT nationality, COUNT(*) as cnt FROM people
                           WHERE nationality != '' GROUP BY nationality ORDER BY cnt DESC LIMIT 10""")
            top_nats = [dict(r) for r in cur.fetchall()]

            cur.execute("""SELECT occupation, COUNT(*) as cnt FROM people
                           WHERE occupation != '' GROUP BY occupation ORDER BY cnt DESC LIMIT 10""")
            top_occs = [dict(r) for r in cur.fetchall()]

            cur.execute("""SELECT category, COUNT(*) as cnt FROM people
                           WHERE category != '' GROUP BY category ORDER BY cnt DESC LIMIT 10""")
            top_cats = [dict(r) for r in cur.fetchall()]

            # Birth century distribution
            cur.execute("""SELECT (birth_year / 100) * 100 as century, COUNT(*) as cnt
                           FROM people WHERE birth_year IS NOT NULL
                           GROUP BY century ORDER BY century""")
            by_century = [dict(r) for r in cur.fetchall()]

            # Gender balance
            cur.execute("""SELECT gender, COUNT(*) as cnt FROM people
                           WHERE gender != '' GROUP BY gender""")
            genders = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT value FROM meta WHERE key = 'last_migration'")
            last_mig = cur.fetchone()
            return {
                "total": total,
                "nationalities": nats,
                "occupations": occs,
                "categories": cats,
                "verified": verified,
                "has_bazi": has_bazi,
                "has_death": has_death,
                "twin_groups": twin_groups,
                "top_nationalities": top_nats,
                "top_occupations": top_occs,
                "top_categories": top_cats,
                "by_century": by_century,
                "genders": genders,
                "last_migration": last_mig["value"] if last_mig else "",
                "db_size_mb": self._db_size_mb(),
            }
        finally:
            conn.close()

    def _db_size_mb(self):
        try:
            return round(os.path.getsize(self.db_path) / 1024 / 1024, 1)
        except OSError:
            return 0.0

    def random(self, n=10):
        rows = self._fetchall(
            "SELECT rowid, * FROM people ORDER BY RANDOM() LIMIT ?", (n,)
        )
        return self._rows_to_list(rows)

    # ── Twin queries ──

    def get_twin_group(self, group_id):
        rows = self._fetchall(
            "SELECT rowid, * FROM people WHERE twin_group_id = ?", (group_id,)
        )
        return self._rows_to_list(rows)

    def get_by_bazi(self, bazi, limit=50):
        """Find people sharing the same BaZi."""
        rows = self._fetchall(
            "SELECT rowid, * FROM people WHERE bazi = ? ORDER BY source_priority DESC LIMIT ?",
            (bazi, limit),
        )
        return self._rows_to_list(rows)

    # ── Cleanup ──

    def rebuild_fts(self):
        """Rebuild full-text search index."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO people_fts(people_fts) VALUES('rebuild')")
            conn.commit()
        finally:
            conn.close()

    def vacuum(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("VACUUM")
            conn.commit()
        finally:
            conn.close()

    def close(self):
        pass  # connections are auto-closed per operation


# ── Convenience ──

_db = None

def get_db():
    global _db
    if _db is None:
        _db = PeopleDatabase()
    return _db

def init_db():
    return get_db()

def migrate_from_master():
    """One-shot: import master_10k.json into SQLite."""
    db = get_db()
    master_path = os.path.join(os.path.dirname(DB_PATH), "master_10k.json")
    if not os.path.exists(master_path):
        print(f"master_10k.json not found at {master_path}")
        return 0
    count = db.import_from_json(master_path)
    db.rebuild_fts()
    db.vacuum()
    s = db.stats()
    print(f"Migrated {count} people. DB: {s['db_size_mb']}MB")
    return count


if __name__ == "__main__":
    import sys
    if "--migrate" in sys.argv:
        migrate_from_master()
    else:
        db = get_db()
        s = db.stats()
        print(f"Database: {s['db_size_mb']}MB, {s['total']} people")
        print(f"  Verified: {s['verified']}, Has BaZi: {s['has_bazi']}, Death: {s['has_death']}")
        print(f"  Nationalities: {s['nationalities']}, Occupations: {s['occupations']}")
        print(f"  Last migration: {s['last_migration']}")
        if s['total'] > 0:
            print("\nSample:")
            for p in db.random(3):
                print(f"  {p['name']}: {p['birth_year']} {p['nationality']} {p['occupation']}")
    sys.exit(0)
