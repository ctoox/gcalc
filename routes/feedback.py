from flask import Blueprint, request, jsonify
from datetime import datetime

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

@feedback_bp.route("", methods=["POST"])
def submit_feedback():
    data = request.json
    return jsonify({
        "id": 1,
        "message": "反馈已收到",
        "timestamp": str(datetime.now())
    }), 201

@feedback_bp.route("", methods=["GET"])
def list_feedback():
    return jsonify({"feedback": [], "total": 0})
