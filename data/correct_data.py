"""
Data correction system for fortune telling.
Allows dynamic correction of person data.
Tracks corrections for audit trail.
"""

import sys, os, json
from datetime import datetime

DATA_DIR = os.path.dirname(__file__)
REAL_FILE = os.path.join(DATA_DIR, "real_people.json")
CORRECTION_LOG = os.path.join(DATA_DIR, "correction_log.json")

def load_correction_log():
    if os.path.exists(CORRECTION_LOG):
        with open(CORRECTION_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"corrections": [], "total_corrections": 0}

def save_correction_log(log):
    with open(CORRECTION_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def load_real_data():
    if not os.path.exists(REAL_FILE):
        return {"persons": []}
    with open(REAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_real_data(data):
    with open(REAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_persons(name=None, birth_year=None, nationality=None, occupation=None, quality_tag=None):
    data = load_real_data()
    results = []
    for p in data.get("persons", []):
        if name and name.lower() not in p.get("name", "").lower():
            continue
        if birth_year and p.get("birth_year") != birth_year:
            continue
        if nationality and nationality.lower() not in p.get("nationality", "").lower():
            continue
        if occupation and occupation.lower() not in p.get("occupation", "").lower():
            continue
        if quality_tag and quality_tag not in p.get("quality_tags", []):
            continue
        results.append(p)
    return results

def correct_person(name, birth_year, field, value, note=""):
    data = load_real_data()
    log = load_correction_log()

    found = False
    for p in data.get("persons", []):
        if p.get("name") == name and p.get("birth_year") == birth_year:
            old_value = p.get(field)
            p[field] = value
            p["corrected"] = True
            p["correction_note"] = note
            log.setdefault("corrections", []).append({
                "name": name,
                "birth_year": birth_year,
                "field": field,
                "old_value": old_value,
                "new_value": value,
                "note": note,
                "timestamp": str(datetime.now()),
            })
            log["total_corrections"] = len(log["corrections"])
            save_correction_log(log)
            save_real_data(data)
            found = True
            print(f"[correct] Fixed {name} ({birth_year}): {field} = {value}")
            break

    if not found:
        print(f"[correct] Person not found: {name} ({birth_year})")
    return found

def mark_disputed(name, birth_year, disputed=True, note=""):
    data = load_real_data()
    for p in data.get("persons", []):
        if p.get("name") == name and p.get("birth_year") == birth_year:
            p["disputed"] = disputed
            p["correction_note"] = note
            save_real_data(data)
            print(f"[correct] Marked {name} ({birth_year}) disputed={disputed}")
            return True
    return False

def set_confidence(name, birth_year, confidence):
    data = load_real_data()
    for p in data.get("persons", []):
        if p.get("name") == name and p.get("birth_year") == birth_year:
            p["confidence"] = confidence
            save_real_data(data)
            print(f"[correct] Set {name} ({birth_year}) confidence={confidence}")
            return True
    return False

def add_quality_tag(name, birth_year, tag):
    data = load_real_data()
    for p in data.get("persons", []):
        if p.get("name") == name and p.get("birth_year") == birth_year:
            tags = p.get("quality_tags", [])
            if tag not in tags:
                tags.append(tag)
                p["quality_tags"] = tags
                save_real_data(data)
                print(f"[correct] Added tag '{tag}' to {name} ({birth_year})")
            return True
    return False

def bulk_correct(search_name=None, search_nationality=None, search_occupation=None,
                 set_field=None, set_value=None, min_confidence=0.0, max_confidence=1.0):
    data = load_real_data()
    log = load_correction_log()
    count = 0
    for p in data.get("persons", []):
        if search_name and search_name.lower() not in p.get("name", "").lower():
            continue
        if search_nationality and search_nationality.lower() not in p.get("nationality", "").lower():
            continue
        if search_occupation and search_occupation.lower() not in p.get("occupation", "").lower():
            continue
        conf = p.get("confidence", 1.0)
        if conf < min_confidence or conf > max_confidence:
            continue
        if set_field:
            old = p.get(set_field)
            p[set_field] = set_value
            p["corrected"] = True
            log.setdefault("corrections", []).append({
                "name": p.get("name"),
                "birth_year": p.get("birth_year"),
                "field": set_field,
                "old_value": old,
                "new_value": set_value,
                "note": "bulk_correct",
                "timestamp": str(datetime.now()),
            })
            count += 1
    if count > 0:
        log["total_corrections"] = len(log.get("corrections", []))
        save_correction_log(log)
        save_real_data(data)
    print(f"[correct] Bulk corrected {count} persons")
    return count

def get_correction_stats():
    log = load_correction_log()
    data = load_real_data()
    persons = data.get("persons", [])
    disputed = sum(1 for p in persons if p.get("disputed"))
    corrected = sum(1 for p in persons if p.get("corrected"))
    low_conf = sum(1 for p in persons if p.get("confidence", 1.0) < 0.8)
    return {
        "total_persons": len(persons),
        "disputed": disputed,
        "corrected": corrected,
        "low_confidence": low_conf,
        "total_corrections": log.get("total_corrections", 0),
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--find", nargs="+", help="Find persons")
    parser.add_argument("--correct", nargs=4, metavar=("NAME", "YEAR", "FIELD", "VALUE"), help="Correct a field")
    parser.add_argument("--disputed", nargs=2, metavar=("NAME", "YEAR"), help="Mark as disputed")
    parser.add_argument("--confidence", nargs=3, metavar=("NAME", "YEAR", "SCORE"), help="Set confidence")
    parser.add_argument("--tag", nargs=3, metavar=("NAME", "YEAR", "TAG"), help="Add quality tag")
    parser.add_argument("--stats", action="store_true", help="Show correction stats")
    args = parser.parse_args()

    if args.stats:
        s = get_correction_stats()
        for k, v in s.items():
            print(f"{k}: {v}")
    elif args.correct:
        correct_person(args.correct[0], int(args.correct[1]), args.correct[2], args.correct[3])
    elif args.disputed:
        mark_disputed(args.disputed[0], int(args.disputed[1]))
    elif args.confidence:
        set_confidence(args.confidence[0], int(args.confidence[1]), float(args.confidence[2]))
    elif args.tag:
        add_quality_tag(args.tag[0], int(args.tag[1]), args.tag[2])
    elif args.find:
        results = find_persons(name=args.find[0] if args.find else None)
        for r in results[:10]:
            print(f"{r.get('name')} ({r.get('birth_year')}) - {r.get('nationality')} - {r.get('occupation')}")
    else:
        print("Use --find, --correct, --disputed, --confidence, --tag, or --stats")
