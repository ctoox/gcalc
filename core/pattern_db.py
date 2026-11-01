"""Statistical pattern database.
Maps BaZi patterns → outcome probabilities. Self-improves as new cases are validated.
Uses similarity matching: given a new BaZi, find the K most similar known cases."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, math, itertools
from pathlib import Path
from collections import defaultdict, Counter

ELEMENTS = ["金", "木", "水", "火", "土"]
ZODIAC = ["rat", "ox", "tiger", "rabbit", "dragon", "snake",
          "horse", "goat", "monkey", "rooster", "dog", "pig"]

class PatternDB:
    def __init__(self, db_path="data/pattern_db.json"):
        self.db_path = Path(db_path)
        # pattern_key -> {outcome_type -> {value -> count}}
        self.patterns = {}
        # raw known cases
        self.cases = []
        self._load()

    def _load(self):
        if self.db_path.exists():
            with open(self.db_path, encoding="utf-8") as f:
                d = json.load(f)
            self.patterns = d.get("patterns", {})
            self.cases = d.get("cases", [])

    def save(self):
        self.db_path.parent.mkdir(exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump({"patterns": self.patterns, "cases": self.cases}, f, ensure_ascii=False, indent=2)

    def _make_key(self, bazi):
        """Create pattern key from BaZi analysis."""
        dm = bazi.get("day_master_element", "?")
        dom = bazi.get("elements", {}).get("dominant", "?")
        miss = tuple(sorted(bazi.get("elements", {}).get("missing", [])))
        all_el = tuple(sorted(bazi.get("elements", {}).get("counts", {}).keys()))
        return f"DM={dm}|DOM={dom}|MISS={miss}|ALL={all_el}"

    def add_case(self, bazi, outcomes):
        """Add a validated case. outcomes = {lifespan, career, wealth, health, ...}"""
        key = self._make_key(bazi)
        if key not in self.patterns:
            self.patterns[key] = {}
        for out_type, out_value in outcomes.items():
            if out_type not in self.patterns[key]:
                self.patterns[key][out_type] = {"total": 0, "values": {}}
            self.patterns[key][out_type]["total"] += 1
            v = str(out_value)
            self.patterns[key][out_type]["values"][v] = self.patterns[key][out_type]["values"].get(v, 0) + 1

        self.cases.append({"key": key, "bazi_summary": {
            "day_master": bazi.get("day_master_element"),
            "dominant": bazi.get("elements", {}).get("dominant"),
            "missing": bazi.get("elements", {}).get("missing"),
            "counts": bazi.get("elements", {}).get("counts"),
        }, "outcomes": outcomes})
        self.save()

    def query(self, bazi, outcome_type="career", k=5):
        """Query most similar patterns. Returns probability distribution + similar cases."""
        key = self._make_key(bazi)
        dm = bazi.get("day_master_element", "?")
        dom = bazi.get("elements", {}).get("dominant", "?")
        miss = set(bazi.get("elements", {}).get("missing", []))

        # Score all known patterns by similarity
        scored = []
        for pkey, pdata in self.patterns.items():
            if outcome_type not in pdata:
                continue
            parts = dict(p.split("=") for p in pkey.split("|"))
            p_dm = parts.get("DM", "?")
            p_dom = parts.get("DOM", "?")
            p_miss = set(parts.get("MISS", "()").strip("()").split(",")) if parts.get("MISS", "()") != "()" else set()
            if p_miss == {""}:
                p_miss = set()

            # Similarity score: exact match = 2, same element = 1, different = 0
            score = 0
            score += 2 if p_dm == dm else (1 if p_dm in ELEMENTS and dm in ELEMENTS else 0)
            score += 2 if p_dom == dom else (1 if p_dom in ELEMENTS and dom in ELEMENTS else 0)
            overlap = len(miss & p_miss)
            score += overlap
            score -= len(miss ^ p_miss) * 0.5
            scored.append((score, pkey, pdata[outcome_type]))

        scored.sort(key=lambda x: -x[0])

        # Aggregate top-k
        result = {"distribution": {}, "similar_cases": [], "confidence": 0}
        total_count = 0
        value_counts = Counter()

        for score, pkey, pdata in scored[:k]:
            for val, cnt in pdata.get("values", {}).items():
                value_counts[val] += cnt * max(1, score)
                total_count += cnt * max(1, score)

        if total_count > 0:
            total_d = sum(value_counts.values())
            result["distribution"] = {v: c / total_d for v, c in value_counts.most_common()}
            top_val, top_cnt = value_counts.most_common(1)[0]
            result["confidence"] = top_cnt / total_d if total_d > 0 else 0

        return result

    def stats(self):
        """Return pattern DB statistics."""
        return {
            "total_patterns": len(self.patterns),
            "total_cases": len(self.cases),
            "outcome_types": list(set(
                ot for p in self.patterns.values() for ot in p.keys()
            ))
        }

    def ingest_validation_figures(self, path="data/validation_enhanced.json"):
        """Seed DB from validation figures."""
        with open(path, encoding="utf-8") as f:
            v = json.load(f)
        figures = v.get("figures", [])
        count = 0
        for fg in figures:
            bazi = {
                "day_master_element": fg.get("day_master", "?"),
                "elements": {
                    "dominant": fg.get("dominant", "?"),
                    "missing": fg.get("missing", []),
                    "counts": {},
                }
            }
            outcomes = {
                "lifespan_category": "长寿" if fg.get("lifespan", 70) >= 75 else "普通" if fg.get("lifespan", 70) >= 60 else "短命",
                "wealth": fg.get("wealth", {}).get("level", "中"),
                "fusion_score": fg.get("fusion_score", 50),
                "social_mobility": fg.get("family", {}).get("social_mobility", "中"),
            }
            self.add_case(bazi, outcomes)
            count += 1
        print(f"[pattern_db] Ingested {count} validation figures")
        return count


if __name__ == "__main__":
    db = PatternDB()
    c = db.ingest_validation_figures()
    print(f"Stats: {db.stats()}")

    # Test query
    sample = {"day_master_element": "水", "elements": {"dominant": "水", "missing": ["火"], "counts": {"水": 3, "金": 1, "木": 1}}}
    result = db.query(sample, "wealth")
    print(f"Query result: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}")
