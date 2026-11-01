from flask import Blueprint, request, jsonify

books_bp = Blueprint("books", __name__, url_prefix="/api/books")

@books_bp.route("", methods=["GET"])
def list_books():
    return jsonify({"books": [], "total": 0})

@books_bp.route("/<int:book_id>", methods=["GET"])
def get_book(book_id):
    return jsonify({"id": book_id, "title": "示例古籍", "entries": []})

@books_bp.route("", methods=["POST"])
def create_book():
    data = request.json
    return jsonify({"id": 1, "title": data.get("title", "")}), 201

@books_bp.route("/<int:book_id>/entries", methods=["GET"])
def list_entries(book_id):
    return jsonify({"entries": [], "total": 0})
