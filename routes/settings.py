from flask import Blueprint, request, jsonify

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

@settings_bp.route("", methods=["GET"])
def get_settings():
    return jsonify({
        "theme": "cosmic",
        "language": "zh-CN",
        "notifications": True
    })

@settings_bp.route("", methods=["PUT"])
def update_settings():
    data = request.json
    return jsonify({"saved": True})

@settings_bp.route("/relationship", methods=["GET"])
def get_relationship_analysis():
    return jsonify({"analysis": "关系分析结果"})
