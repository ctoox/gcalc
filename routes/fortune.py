"""Fortune report API v2 — streaming SSE + FusionV2 + feedback loop."""
import time, json, os, sys
from flask import Blueprint, request, Response, stream_with_context, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.fusion_v2 import FusionV2
from core.pattern_db import PatternDB
from core.calibrator import Calibrator, load_validation_figures
from core.differentiator import DestinyDifferentiator
from core.input_sanitizer import sanitize_name, validate_date, make_id, compute_signature
from core.life_report import LifeReport, calc_da_yun
from core.llm_enhancer import enhance_report
from datetime import date, datetime

fortune_bp = Blueprint("fortune", __name__, url_prefix="/api/fortune")
engine = FusionV2()
pattern_db = PatternDB()
calibrator = Calibrator()
differentiator = DestinyDifferentiator()


@fortune_bp.route("/report", methods=["GET"])
def report():
    y = request.args.get("year", 0, type=int)
    m = request.args.get("month", 1, type=int)
    d = request.args.get("day", 1, type=int)
    h = request.args.get("hour", 12, type=int)
    name_raw = request.args.get("name", "", type=str)
    gender = request.args.get("gender", "男", type=str)
    mode = request.args.get("mode", "comprehensive", type=str)  # standard | comprehensive
    personal_code = request.args.get("code", "", type=str)  # unique per-user code

    # ── Input sanitization ──
    name, name_err = sanitize_name(name_raw)
    if name_err:
        return jsonify({"error": name_err, "code": "INVALID_NAME"}), 400

    date_valid, date_err = validate_date(y, m, d, h)
    if not date_valid:
        return jsonify({"error": date_err, "code": "INVALID_DATE"}), 400

    input_id = make_id(name, y, m, d, h, personal_code)

    llm = request.args.get("llm", "0", type=str) in ("1", "true", "yes")  # enable LLM enhancement

    if mode == "comprehensive":
        lr = LifeReport()
        report = lr.generate(y, m, d, h, name, gender, personal_code=personal_code)
        report["input_id"] = input_id
        if llm:
            report = enhance_report(report)
        report["signature"] = compute_signature(name, y, m, d, h, report.get("bazi_summary", {}).get("八字", ""), personal_code)
        return jsonify(report)
    else:
        r = engine.analyze(y, m, d, h, name, gender, personal_code=personal_code)
        r["input_id"] = input_id
        if llm:
            r = enhance_report(r)
        bazi_str = r.get("chinese", {}).get("bazi", "")
        r["signature"] = compute_signature(name, y, m, d, h, bazi_str, personal_code)
        return jsonify(r)


@fortune_bp.route("/feedback", methods=["POST"])
def feedback():
    """User provides known outcome → pattern DB learns → triggers re-calibration."""
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "")
    y = data.get("year", 0)
    m = data.get("month", 1)
    d = data.get("day", 1)
    h = data.get("hour", 12)

    outcomes = {
        "career_domain": data.get("career_domain", ""),
        "wealth_level": data.get("wealth_level", "中"),
        "lifespan": data.get("lifespan", 0),
        "social_mobility": data.get("social_mobility", "中"),
        "accuracy_rating": data.get("accuracy_rating", 5),
        "user_comment": data.get("comment", ""),
    }

    from core.bazi import BaziEngine
    from datetime import date
    bazi = BaziEngine().calculate(y, m, d, h)
    pattern_db.add_case(bazi, outcomes)

    # Trigger re-calibration every 10 feedbacks
    st = pattern_db.stats()
    if st["total_cases"] % 10 == 0:
        try:
            figures = load_validation_figures()
            calibrator.calibrate(figures, iterations=600)
        except Exception as e:
            pass  # Silently continue if calibration fails mid-flight

    return {
        "status": "ok",
        "total_patterns": st["total_patterns"],
        "total_cases": st["total_cases"],
        "msg": "反馈已记录，系统将持续学习改进。",
    }


@fortune_bp.route("/status", methods=["GET"])
def status():
    meta = engine.metadata()
    return {
        "version": meta["version"],
        "accuracy": meta["accuracy"],
        "patterns": meta["pattern_count"],
        "cases": meta["case_count"],
        "calibrations": meta["calibration_count"],
    }


@fortune_bp.route("/calibrate", methods=["POST"])
def trigger_calibrate():
    try:
        figures = load_validation_figures()
        result = calibrator.calibrate(figures, iterations=1200)
        return {"status": "ok", "accuracy": result["accuracy"]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@fortune_bp.route("/compare", methods=["GET"])
def compare():
    """Compare same birth time in different locations/genders/names.
    Answers: 'Would I be like Kennedy if born same time?'"""
    year = request.args.get("year", 0, type=int)
    month = request.args.get("month", 1, type=int)
    day = request.args.get("day", 1, type=int)
    hour = request.args.get("hour", 12, type=int)
    minute = request.args.get("minute", 0, type=int)
    city = request.args.get("city", "北京", type=str)
    gender = request.args.get("gender", "男", type=str)
    name = request.args.get("name", "", type=str)
    ref_name = request.args.get("ref_name", "", type=str)
    ref_city = request.args.get("ref_city", "", type=str)
    ref_gender = request.args.get("ref_gender", "", type=str)

    if ref_city and ref_name:
        # Two-person comparison
        result = differentiator.differentiate_same_name(
            name=name,
            birth_data={"year": year, "month": month, "day": day,
                        "hour": hour, "minute": minute, "city": city, "gender": gender},
            ref_birth={"year": year, "month": month, "day": day,
                       "hour": hour, "minute": minute, "city": ref_city, "gender": ref_gender or gender},
        )
    else:
        # Destiny fork report
        result = differentiator.destiny_fork_report(
            year, month, day, hour, minute, city, gender, name
        )
    return result


@fortune_bp.route("/twins", methods=["GET"])
def twins():
    """Analyze twin differentiation."""
    year = request.args.get("year", 0, type=int)
    month = request.args.get("month", 1, type=int)
    day = request.args.get("day", 1, type=int)
    hour = request.args.get("hour", 12, type=int)
    min1 = request.args.get("min1", 0, type=int)
    min2 = request.args.get("min2", 5, type=int)
    city = request.args.get("city", "北京", type=str)
    gender1 = request.args.get("gender1", "男", type=str)
    gender2 = request.args.get("gender2", "女", type=str)
    order = request.args.get("order", 1, type=int)

    result = differentiator.differentiate_twins(
        year, month, day, hour, min1, min2, city, gender1, gender2, order
    )
    return result


def _stream_report(y, m, d, h, name, gender, rank):
    def gen():
        r = engine.analyze(y, m, d, h, name, gender, rank)
        fs = r["fusion"]
        b = r["chinese"]
        w = r["western"]
        score = fs["score"]
        dm = b.get("day_master_element", "?")
        miss = b.get("elements", {}).get("missing", [])

        lines = [
            f"【{name or '未知'}命理报告】\n{'='*40}\n",
            f"综合评分: {score}/100  (校准v{fs['calibration_version']}, 置信±{fs['confidence_interval']:.0f})\n",
        ]
        # Honest assessment
        if score >= 80:
            lines.append("▎总体: 上等命格。东西方命理高度统一，五行流通。\n")
        elif score >= 65:
            lines.append("▎总体: 中上命格。有潜力亦有挑战，扬长避短可成事。\n")
        elif score >= 45:
            lines.append("▎总体: 中等命格。利弊参半，需后天努力弥补先天。\n")
        else:
            lines.append("▎总体: 命格偏弱。五行失衡，需大运扶持或贵人相助。\n")

        lines.append(f"\n八字: {b.get('bazi', '?')}\n日主: {dm} | 旺: {b.get('elements',{}).get('dominant','?')} | 缺: {'/'.join(miss) if miss else '俱全'}\n")
        lines.append(f"性格: {b.get('personality', '?')}\n")
        lines.append(f"财富: {b.get('wealth_potential',{}).get('level','?')} (分{b.get('wealth_potential',{}).get('score',0)})\n")

        lines.append(f"\n事业交集: {', '.join(r['career']['overlap'][:3]) or '无直接交集'}\n")
        lines.append(f"八字倾向: {'/'.join(r['career']['east_affinity'])}\n")
        lines.append(f"占星倾向: {'/'.join(r['career']['west_affinity'])}\n")

        lines.append(f"\n占星: 太阳{w.get('sun_sign','?')} | 月亮{w.get('moon_sign','?')} | 上升{w.get('rising_sign','?')}\n")
        lines.append(f"元素: {w.get('element','?')} | 平衡: {', '.join(f'{k}={v}' for k,v in w.get('element_balance',{}).items())}\n")

        lines.append(f"\n寿命参考: {r['lifespan']['estimate']}岁\n")
        lines.append(f"出身: {b.get('family',{}).get('element_vs_family','?')}\n")
        lines.append(f"社会流动: {b.get('family',{}).get('social_mobility','?')}\n")

        # Show statistical evidence if available
        se = r["statistical_evidence"]
        if se["total_cases"] > 0:
            lines.append(f"\n统计样本: {se['total_cases']}个历史案例, {se['total_patterns']}种命局模式\n")
            lines.append(f"财富参考: {list(se.get('wealth',{}).keys())}\n")

        # Honest flaws section
        weak = []
        if miss:
            weak.append(f"缺{'/'.join(miss)}")
        if b.get("wealth_potential",{}).get("level") == "低":
            weak.append("财星弱")
        if abs(fs["east_score"] - fs["west_score"]) > 20:
            weak.append("东西方命理冲突")
        if score < 50:
            weak.append("命格偏弱")
        lines.append(f"\n短板: {' | '.join(weak) if weak else '无明显缺陷'}\n")

        lines.append(f"\n系统精度: {fs['accuracy']:.1f}% (基于{fs['calibration_version']}次校准)\n")

        for sec in lines:
            yield f"data: {json.dumps({'text': sec})}\n\n"
            time.sleep(0.05)

        yield f"data: {json.dumps({'done': True, 'score': score})}\n\n"

    return Response(stream_with_context(gen()), mimetype="text/event-stream")


def _format_report(r, name):
    """Non-streaming JSON report."""
    fs = r["fusion"]
    b = r["chinese"]
    w = r["western"]
    return {
        "name": name,
        "fusion_score": fs["score"],
        "accuracy": fs["accuracy"],
        "confidence_interval": fs["confidence_interval"],
        "calibration_version": fs["calibration_version"],
        "bazi": b.get("bazi"),
        "day_master": b.get("day_master_element"),
        "elements": b.get("elements"),
        "personality": b.get("personality"),
        "wealth": b.get("wealth_potential"),
        "sun_sign": w.get("sun_sign"),
        "career_overlap": r["career"]["overlap"],
        "lifespan_estimate": r["lifespan"]["estimate"],
        "statistical_evidence": r["statistical_evidence"],
        "qimen": r.get("qimen"),
        "family": r.get("family"),
        "yearly": r.get("yearly"),
        "life_timeline": r.get("life_timeline"),
    }
