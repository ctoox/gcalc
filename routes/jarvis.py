from flask import Blueprint, request, jsonify

jarvis_bp = Blueprint("jarvis", __name__, url_prefix="/api/jarvis")

@jarvis_bp.route("/daily", methods=["POST"])
def daily_schedule():
    data = request.json
    return jsonify({
        "date": data.get("date", "2026-07-26"),
        "schedule": [
            {"time": "08:00", "event": "晨会", "fortune": "吉"},
            {"time": "10:00", "event": "重要决策", "fortune": "中吉"},
            {"time": "14:00", "event": "商务洽谈", "fortune": "凶"}
        ],
        "advice": "今日宜静不宜动"
    })

@jarvis_bp.route("/reminders", methods=["GET"])
def reminders():
    return jsonify({"reminders": [], "total": 0})
