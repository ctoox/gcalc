"""Extended calibration: use all 10,164 people from SQLite for validation.
Pre-computes BaZi + Western charts once, then runs evolutionary weight optimization."""
import sys, os, json, time, random, math
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.db import get_db
from core.bazi import BaziEngine
from core.western import WesternEngine
from core.calibrator import Calibrator
from datetime import date

def load_from_db(limit=None):
    """Load validation figures from SQLite database."""
    db = get_db()
    conn = db._connect()
    cur = conn.cursor()

    if limit:
        cur.execute("SELECT * FROM people ORDER BY source_priority DESC, RANDOM() LIMIT ?", (limit,))
    else:
        cur.execute("SELECT * FROM people")

    be = BaziEngine()
    we = WesternEngine()

    figures = []
    errors = 0
    for row in cur.fetchall():
        p = dict(row)
        name = p.get("name", "")
        y = p.get("birth_year")
        m = p.get("birth_month")
        d = p.get("birth_day")
        h = p.get("birth_hour")
        if not all([y, m, d]):
            errors += 1
            continue
        if y is None or y == 0 or y < -5000 or y > 2026:
            errors += 1
            continue

        # Skip ancient people (BC dates cause date() errors)
        if y < 1:
            errors += 1
            continue

        # Safer hour default
        if h is None or h > 23 or h < 0:
            h = 12

        try:
            bazi = be.calculate(y, m, d, h)
            western = we.calculate_chart(date(y, m, d), h)
        except Exception as e:
            errors += 1
            continue

        occ = p.get("occupation", "")
        death_y = p.get("death_year")
        lifespan = death_y - y if death_y and y and death_y > y else 0

        # Map occupation to career domain
        domain_map = Calibrator.CAREER_DOMAIN
        actual_careers = []
        if occ and occ in domain_map:
            actual_careers = [occ]

        fig = {
            "name": name,
            "birth_year": y,
            "birth_month": m,
            "birth_day": d,
            "birth_hour": h,
            "bazi_result": bazi,
            "western_result": western,
            "actual_careers": actual_careers,
            "actual_wealth_level": "中",
            "lifespan": lifespan,
            "family": {"social_mobility": "中"},
            "source": p.get("source", ""),
            "nationality": p.get("nationality", ""),
            "gender": p.get("gender", ""),
        }
        figures.append(fig)

    conn.close()
    print(f"Loaded {len(figures)} figures from DB ({errors} skipped)")
    return figures

def calibrate_with_db(iterations=2000, fig_limit=None):
    """Full calibration using database figures."""
    t0 = time.time()
    figures = load_from_db(limit=fig_limit)
    print(f"Load time: {time.time()-t0:.1f}s")

    if len(figures) < 10:
        print("Not enough figures, aborting")
        return

    c = Calibrator()
    result = c.calibrate(figures, iterations=iterations)
    print(f"\n{'='*50}")
    print(f"Calibration result:")
    print(f"  Accuracy: {result['accuracy']:.2f}%")
    print(f"  Baseline: {result['baseline']:.2f}%")
    print(f"  Improvement: +{result['improvement']:.2f}%")
    print(f"  Weights: {json.dumps(c.params['weights'], ensure_ascii=False)}")
    print(f"  Penalties: {json.dumps(c.params['penalties'], ensure_ascii=False)}")
    print(f"  Bonuses: {json.dumps(c.params['bonuses'], ensure_ascii=False)}")
    print(f"  Total time: {time.time()-t0:.0f}s")
    print(f"{'='*50}")

    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter", type=int, default=2000, help="Optimization iterations")
    parser.add_argument("--limit", type=int, default=None, help="Limit people to load")
    args = parser.parse_args()
    calibrate_with_db(iterations=args.iter, fig_limit=args.limit)
