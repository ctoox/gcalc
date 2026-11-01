"""12 时辰 analyzer: try all possible birth hours, pick the best match.
Scoring uses career domain match + lifespan match + internal consistency."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.fusion_v2 import FusionV2
from core.bazi import BaziEngine
from core.western import WesternEngine
from core.calibrator import Calibrator
from datetime import date as _date

SHICHEN = [
    (23, "子"), (1, "丑"), (3, "寅"), (5, "卯"),
    (7, "辰"), (9, "巳"), (11, "午"), (13, "未"),
    (15, "申"), (17, "酉"), (19, "戌"), (21, "亥"),
]

# Career domain mapping (from calibrator)
DOMAIN_MAP = {}
for domain, keywords in Calibrator.BAZI_CAREER_DOMAIN.items():
    for kw in keywords:
        DOMAIN_MAP[kw] = domain

class ShiChenAnalyzer:
    def __init__(self):
        self.engine = FusionV2()
        self.be = BaziEngine()
        self.we = WesternEngine()

    def analyze_all(self, year, month, day, name="", gender="男", actual_occupation=None, actual_lifespan=None):
        """Try all 12 时辰, score each by how well predictions match known facts."""
        results = []
        for hour, sc_name in SHICHEN:
            try:
                bazi = self.be.calculate(year, month, day, hour)
                western = self.we.calculate_chart(_date(year, month, day), hour)
                fusion = self.engine.analyze(year, month, day, hour, name, gender, rank=2)
                fs = fusion["fusion"]
                bazi_el = bazi.get("elements", {})

                # Base scores
                east = fs["east_score"]
                west = fs["west_score"]
                score = fs["score"]

                # ── Career match score ──
                career_match = 0
                if actual_occupation:
                    pred_careers = fusion["career"].get("overlap", []) + fusion["career"].get("all", [])
                    # Check if predicted career domain matches actual
                    actual_domain = DOMAIN_MAP.get(actual_occupation, "")
                    for c in pred_careers:
                        for kw, dom in DOMAIN_MAP.items():
                            if kw in c and dom == actual_domain:
                                career_match = 50
                                break
                        if career_match > 0:
                            break
                    if not career_match:
                        # Partial: check built-in career domain map
                        actual_dom = Calibrator.CAREER_DOMAIN.get(actual_occupation, "")
                        for c in pred_careers[:6]:
                            for kw, dom in DOMAIN_MAP.items():
                                if kw in c:
                                    if dom == actual_dom:
                                        career_match = 40
                                    break

                # ── Lifespan match score ──
                lifespan_match = 0
                if actual_lifespan and actual_lifespan > 0:
                    pred_ls = fusion["lifespan"]["estimate"]
                    diff = abs(pred_ls - actual_lifespan)
                    lifespan_match = max(0, 30 - diff * 2)  # lose 2 pts per year off

                # ── Internal consistency ──
                ew_diff = abs(east - west)
                consistency = max(0, 30 - ew_diff * 0.5)

                # ── Element balance ──
                missing = bazi_el.get("missing", [])
                balance = max(0, 20 - len(missing) * 5)

                # ── Total weighted score ──
                # Heavier weight on career match if known, otherwise fall back to consistency
                if actual_occupation or actual_lifespan:
                    total_score = career_match + lifespan_match + consistency + balance
                else:
                    total_score = consistency * 2 + balance * 2 + score * 0.2

                results.append({
                    "时辰": f"{sc_name}时",
                    "hour": hour,
                    "bazi": bazi.get("bazi", ""),
                    "day_master": bazi.get("day_master_element", ""),
                    "missing": [m for m in missing],
                    "dominant": bazi_el.get("dominant", ""),
                    "score": round(score, 1),
                    "east": round(east, 1),
                    "west": round(west, 1),
                    "career_match": round(career_match, 1),
                    "lifespan_match": round(lifespan_match, 1),
                    "total_score": round(total_score, 1),
                    "personality": bazi.get("personality", ""),
                    "career": fusion["career"].get("overlap", [])[:3],
                    "predicted_careers": fusion["career"].get("all", [])[:4],
                    "lifespan": fusion["lifespan"].get("estimate", ""),
                    "wealth": fusion["wealth"].get("level", ""),
                })
            except Exception as e:
                results.append({
                    "时辰": f"{sc_name}时",
                    "hour": hour,
                    "error": str(e),
                    "total_score": 0,
                    "score": 0,
                })

        results.sort(key=lambda r: -r["total_score"])
        return results

    def best_match(self, year, month, day, name="", gender="男", actual_occupation=None, actual_lifespan=None):
        results = self.analyze_all(year, month, day, name, gender, actual_occupation, actual_lifespan)
        return results[0] if results else None

    def validate_against_db(self, sample_size=100):
        """Test accuracy: hide known birth hour, use career+lifespan from DB to pick correct 时辰."""
        from core.db import get_db
        db = get_db()
        conn = db._connect()
        cur = conn.cursor()

        cur.execute("""SELECT name, birth_year, birth_month, birth_day, birth_hour,
                              gender, occupation, death_year
                       FROM people
                       WHERE birth_hour IS NOT NULL AND birth_hour >= 0 AND birth_hour <= 23
                       AND birth_year > 1800 AND birth_year < 2020
                       AND occupation != '' AND occupation IS NOT NULL
                       ORDER BY RANDOM() LIMIT ?""", (sample_size,))

        rows = cur.fetchall()
        conn.close()

        correct = 0
        total = 0
        details = []
        confusion = {}

        for row in rows:
            p = dict(row)
            name = p["name"]
            y, m, d = p["birth_year"], p["birth_month"], p["birth_day"]
            true_hour = p["birth_hour"]
            gender = p.get("gender", "男")
            occ = p.get("occupation", "")
            death = p.get("death_year")
            lifespan = death - y if death and y and death > y else None

            # Map true hour to 时辰 name
            true_sc = "子"
            for hour, sc_name in SHICHEN:
                if true_hour == hour:
                    true_sc = sc_name
                    break

            results = self.analyze_all(y, m, d, name, gender, occ, lifespan)
            if not results:
                continue

            best = results[0]
            best_sc = best["时辰"].replace("时", "")
            is_correct = best_sc == true_sc
            if is_correct:
                correct += 1
            total += 1

            # Confusion matrix
            key = f"{true_sc}->{best_sc}"
            confusion[key] = confusion.get(key, 0) + 1

            details.append({
                "name": name,
                "true_hour": true_hour,
                "true_sc": f"{true_sc}时",
                "best_sc": best["时辰"],
                "correct": is_correct,
                "score": best["total_score"],
                "career_match": best.get("career_match", 0),
                "lifespan_match": best.get("lifespan_match", 0),
            })

        accuracy = correct / total * 100 if total > 0 else 0
        return {
            "total": total,
            "correct": correct,
            "accuracy": round(accuracy, 1),
            "top_confusions": sorted(confusion.items(), key=lambda x: -x[1])[:15],
            "details": details[:30],
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", type=int, default=0, help="Validate against N DB people")
    parser.add_argument("--year", type=int, help="Birth year")
    parser.add_argument("--month", type=int, help="Birth month")
    parser.add_argument("--day", type=int, help="Birth day")
    parser.add_argument("--name", default="", help="Person name")
    args = parser.parse_args()

    a = ShiChenAnalyzer()

    if args.validate:
        result = a.validate_against_db(args.validate)
        print(f"Validation: {result['correct']}/{result['total']} correct = {result['accuracy']}%")
        for d in result["details"][:10]:
            status = "OK" if d["correct"] else "X"
            print(f"  {status} {d['name']}: true={d['true_sc']} best={d['best_sc']} score={d['score']}")
    elif args.year:
        results = a.analyze_all(args.year, args.month, args.day, args.name)
        print(f"\nAll 12 时辰 for {args.name or 'unknown'} ({args.year}-{args.month:02d}-{args.day:02d}):")
        print(f"{'时辰':>6} | {'八字':>20} | {'日主':>4} | {'缺':>6} | {'评分':>6} | {'置信':>6} | {'事业':>20}")
        print("-" * 80)
        for r in results:
            miss = "/".join(r["missing"]) if r["missing"] else "无"
            career = ",".join(r["career"]) if r.get("career") else ""
            print(f"{r['时辰']:>6} | {r['bazi']:>20} | {r['day_master']:>4} | {miss:>6} | {r['score']:>5.1f} | {r['confidence']:>5.1f} | {career:>20}")
        print(f"\nBest match: {results[0]['时辰']} (confidence {results[0]['confidence']})")
    else:
        print("Use --validate N or --year Y --month M --day D [--name N]")
