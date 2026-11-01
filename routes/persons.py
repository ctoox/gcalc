"""People API — backed by SQLite. Full-text search, filter, paginate."""
import sys, os
from flask import Blueprint, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db

persons_bp = Blueprint("persons", __name__, url_prefix="/api/persons")


@persons_bp.route("", methods=["GET"])
def list_persons():
    db = get_db()
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    sort_by = request.args.get("sort", "name")

    if q:
        results, total = db.search(q, limit=per_page, offset=(page - 1) * per_page)
    else:
        results, total = db.filter(
            nationality=request.args.get("nationality"),
            occupation=request.args.get("occupation"),
            category=request.args.get("category"),
            year_from=request.args.get("year_from", type=int),
            year_to=request.args.get("year_to", type=int),
            gender=request.args.get("gender"),
            source=request.args.get("source"),
            verified=request.args.get("verified", type=bool),
            page=page,
            per_page=per_page,
            sort_by=sort_by,
        )

    return jsonify({
        "persons": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total else 0,
    })


@persons_bp.route("/stats", methods=["GET"])
def stats():
    db = get_db()
    return jsonify(db.stats())


@persons_bp.route("/<person_id>", methods=["GET"])
def get_person(person_id):
    db = get_db()
    p = db.get(person_id)
    if p:
        return jsonify(p)
    return jsonify({"error": "not found"}), 404


@persons_bp.route("/<person_id>", methods=["PUT"])
def update_person(person_id):
    data = request.json or {}
    db = get_db()
    existing = db.get(person_id)
    if not existing:
        return jsonify({"error": "not found"}), 404
    data["id"] = person_id
    for k, v in data.items():
        existing[k] = v
    db.insert(existing)
    return jsonify({"id": person_id, "updated": True})


@persons_bp.route("/<person_id>", methods=["DELETE"])
def delete_person(person_id):
    db = get_db()
    db.delete(person_id)
    return jsonify({"deleted": True})


@persons_bp.route("/bazi/<bazi_code>", methods=["GET"])
def by_bazi(bazi_code):
    """Find all people sharing the same BaZi."""
    db = get_db()
    results = db.get_by_bazi(bazi_code, limit=100)
    return jsonify({"total": len(results), "persons": results})


@persons_bp.route("/twin/<group_id>", methods=["GET"])
def twin_group(group_id):
    db = get_db()
    results = db.get_twin_group(group_id)
    return jsonify({"total": len(results), "persons": results})


@persons_bp.route("/random", methods=["GET"])
def random():
    n = request.args.get("n", 5, type=int)
    n = min(n, 100)
    db = get_db()
    results = db.random(n)
    return jsonify({"total": len(results), "persons": results})
