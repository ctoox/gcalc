from flask import Blueprint, request, jsonify
import sys, os, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import get_db

control_bp = Blueprint("collector", __name__, url_prefix="/api/collector")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONTROL_FILE = os.path.join(DATA_DIR, "control.json")
STATE_FILE = os.path.join(DATA_DIR, "slow_state.json")
REAL_FILE = os.path.join(DATA_DIR, "real_people.json")
CHINA_STATE = os.path.join(DATA_DIR, "china_state.json")
EDGE_STATE = os.path.join(DATA_DIR, "edge_state.json")
TRAINING_LOG = os.path.join(DATA_DIR, "training_log.json")

def _read_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _get_quality_stats():
    from core.db import get_db
    db = get_db()
    s = db.stats()
    return {
        "total": s["total"],
        "chinese": 0,
        "verified": s["verified"],
        "disputed": 0,
        "avg_confidence": 0.7,
        "quality_tags": {},
    }

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@control_bp.route("/status", methods=["GET"])
def status():
    control = _read_json(CONTROL_FILE)
    state = _read_json(STATE_FILE)
    china_state = _read_json(CHINA_STATE)
    edge_state = _read_json(EDGE_STATE)
    quality = _get_quality_stats()
    total = quality["total"]
    training = _read_json(TRAINING_LOG)
    return jsonify({
        "paused": control.get("paused", False),
    "delay_seconds": control.get("delay_seconds", 5.0),
    "threads": control.get("threads", 10),
    "target_total": control.get("target_total", 0),
    "max_offset": control.get("max_offset", 0),
    "total_collected": total,
    "current_offset": state.get("offset", 0),
    "collector_state_offset": state.get("offset", 0),
    "collector_total": state.get("total", 0),
    "updated": control.get("updated", state.get("updated", "")),
    "rate_label": _rate_label(control.get("delay_seconds", 5), control.get("threads", 10)),
    "stop": control.get("stop", False),
    "china_offset": china_state.get("offset", 0),
    "china_total": china_state.get("total", 0),
    "edge_offset": edge_state.get("offsets", {}),
    "edge_total": edge_state.get("total", 0),
    "quality": quality,
    "training_batches": len(training.get("batches", [])),
    "training_total": training.get("total_trained", 0),
    })

@control_bp.route("/stop", methods=["POST"])
def stop_collector():
    ctrl = _read_json(CONTROL_FILE)
    ctrl["stop"] = True
    ctrl["paused"] = True
    ctrl["updated"] = str(datetime.now())
    _write_json(CONTROL_FILE, ctrl)
    return jsonify({"ok": True, "stop": True})

@control_bp.route("/control", methods=["GET", "POST", "PUT"])
def control():
    if request.method == "GET":
        return status()
    data = request.get_json(silent=True) or {}
    control = _read_json(CONTROL_FILE)
    changed = []
    if "paused" in data:
        control["paused"] = bool(data["paused"])
        changed.append(f"paused={control['paused']}")
    if "delay" in data:
        d = max(0.5, float(data["delay"]))
        control["delay_seconds"] = d
        changed.append(f"delay={d}s")
    if "threads" in data:
        t = max(1, min(50, int(data["threads"])))
        control["threads"] = t
        changed.append(f"threads={t}")
    if "target" in data:
        t = int(data["target"])
        control["target_total"] = t
        changed.append(f"target={t}")
    if "max_offset" in data:
        m = int(data["max_offset"])
        control["max_offset"] = m
        changed.append(f"max_offset={m}")
    control["updated"] = str(datetime.now())
    _write_json(CONTROL_FILE, control)
    return jsonify({"ok": True, "changed": changed, "control": control})

@control_bp.route("/pause", methods=["POST"])
def pause():
    ctrl = _read_json(CONTROL_FILE)
    if ctrl.get("paused"):
        return jsonify({"ok": True, "paused": True, "idempotent": True})
    ctrl["paused"] = True
    ctrl["updated"] = str(datetime.now())
    _write_json(CONTROL_FILE, ctrl)
    return jsonify({"ok": True, "paused": True})

@control_bp.route("/resume", methods=["POST"])
def resume():
    ctrl = _read_json(CONTROL_FILE)
    if not ctrl.get("paused"):
        return jsonify({"ok": True, "paused": False, "idempotent": True})
    ctrl["paused"] = False
    ctrl["updated"] = str(datetime.now())
    _write_json(CONTROL_FILE, ctrl)
    return jsonify({"ok": True, "paused": False})

@control_bp.route("/set_delay", methods=["POST"])
def set_delay():
    data = request.get_json(silent=True) or {}
    delay = max(1.0, float(data.get("delay", 12)))
    _write_json(CONTROL_FILE, {**(_read_json(CONTROL_FILE)), "delay_seconds": delay, "updated": str(datetime.now())})
    return jsonify({"ok": True, "delay_seconds": delay})

def _rate_label(delay, threads=10):
    throughput = threads / max(delay, 1)
    if throughput >= 10:
        return f"ludicrous ({throughput:.0f}/s)"
    elif throughput >= 3:
        return f"fast ({throughput:.1f}/s)"
    elif throughput >= 1:
        return f"normal ({throughput:.1f}/s)"
    elif throughput >= 0.3:
        return f"slow ({throughput:.1f}/s)"
    else:
        return f"glacial ({throughput:.2f}/s)"
