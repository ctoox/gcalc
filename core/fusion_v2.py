"""Fusion v2 — Bayesian fusion engine with calibrated weights + statistical priors.
Goal: approach 99.99999% accuracy through continuous self-improvement."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from core.bazi import BaziEngine
from core.western import WesternEngine
from datetime import date
_bazi_engine = BaziEngine()
_western_engine = WesternEngine()
from core.calibrator import Calibrator, load_validation_figures
from core.pattern_db import PatternDB
from core.yearly import YearlyEngine
from core.qimen import QiMenEngine
from core.family_deep import FamilyDeepAnalyzer
import importlib.util, sys
_spec = importlib.util.spec_from_file_location("life_collector",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "life_collector.py"))
_lc_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lc_mod)
LifeCollector = _lc_mod.LifeCollector

class FusionV2:
    def __init__(self):
        self.calibrator = Calibrator()
        self.pattern_db = PatternDB()
        self.yearly = YearlyEngine()
        self.qimen = QiMenEngine()
        self.family_deep = FamilyDeepAnalyzer()
        self.life_collector = LifeCollector()
        self._calibrated = False

    def ensure_calibrated(self, force=False):
        """Run calibration if not yet done or accuracy is low.
        Always seeds pattern DB if empty. Reloads pattern DB each call."""
        if force or self.calibrator.params["calibration_count"] == 0:
            figures = load_validation_figures()
            if figures:
                self.calibrator.calibrate(figures, iterations=600)
        # Reload pattern DB from disk (feedback may have added data)
        self.pattern_db = PatternDB()
        # Seed if still empty
        if self.pattern_db.stats()["total_cases"] == 0:
            self.pattern_db.ingest_validation_figures()
        self._calibrated = True

    def analyze(self, y, m, d, h=12, name="", gender="男", rank=2, personal_code=""):
        """Full analysis with calibrated fusion. Returns complete profile.
        personal_code: unique code per user to differentiate identical birth data + names."""
        self.ensure_calibrated()

        bazi = _bazi_engine.calculate(y, m, d, h)
        western = _western_engine.calculate_chart(date(y, m, d), h)

        w = self.calibrator.params

        # ---- Component scores ----
        # ---- Name 五行 influence (same birth data + different name = different score) ----
        name_score = 50
        name_element_influence = ""
        name_hash = ""
        if name:
            from core.input_sanitizer import name_stroke_element
            nse = name_stroke_element(name)
            ne = nse.get("total_element", "") or nse.get("dominant_element", "")
            dm = bazi.get("day_master_element", "")
            ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
            hash_score = nse.get("hash_score", 50)
            sec_el = nse.get("secondary_element", "土")
            if ne and dm:
                if sheng.get(ne) == dm:
                    name_score = 30 + hash_score * 0.4
                    name_element_influence = f"{ne}生日主{dm}"
                elif ke.get(ne) == dm:
                    name_score = 10 + hash_score * 0.3
                    name_element_influence = f"{ne}克日主{dm}"
                elif ne == dm:
                    name_score = 20 + hash_score * 0.5
                    name_element_influence = f"{ne}同日主{dm}"
                else:
                    name_score = 15 + hash_score * 0.5
                    name_element_influence = f"{ne}与日主{dm}"
            else:
                name_score = hash_score * 0.6
                name_element_influence = "姓名命理影响"
            # Secondary element nuance
            if sec_el == dm:
                name_score -= 3
            elif sheng.get(sec_el) == dm:
                name_score += 5
            name_score = max(10, min(90, name_score))
            name_hash = nse.get("hash_score", 0)

        # ---- Personal code influence (unique per-user disambiguation) ----
        pc_offset = 0.0
        pc_desc = ""
        if personal_code:
            from core.input_sanitizer import personal_code_influence
            pc_offset, pc_desc = personal_code_influence(personal_code)

        east_score = self._score_bazi(bazi, w)
        west_score = self._score_western(western, w)
        num_score = self._score_numerology(western, w)

        # ---- Statistical priors ----
        stat_wealth = self.pattern_db.query(bazi, "wealth")
        stat_lifespan = self.pattern_db.query(bazi, "lifespan_category")
        stat_fusion = self.pattern_db.query(bazi, "fusion_score")

        stat_score = 50
        if stat_wealth.get("distribution"):
            top_w = max(stat_wealth["distribution"], key=stat_wealth["distribution"].get)
            wealth_pct = {"低": 25, "中": 50, "高": 75}.get(top_w, 50)
            stat_score = stat_score * 0.7 + wealth_pct * 0.3
        if stat_fusion.get("distribution"):
            avg_f = sum(float(k) * v for k, v in stat_fusion["distribution"].items())
            stat_score = stat_score * 0.7 + avg_f * 0.3

        # ---- Name score (~10% influence) ----
        nw_name = 0.8
        # ---- Bayesian fusion ----
        cw = w.get("weights", {})
        ew = cw.get("chinese", 1.0)
        ww = cw.get("western", 1.0)
        nw = cw.get("numerology", 1.0)
        sw = cw.get("statistical", 1.0)
        total_w = ew + ww + nw + sw + nw_name

        fusion_raw = (east_score * ew + west_score * ww + num_score * nw + stat_score * sw + name_score * nw_name) / total_w

        # Penalties and bonuses
        penalty = 0
        miss = len(bazi.get("elements", {}).get("missing", []))
        penalty += miss * w["penalties"]["missing_element"]

        if abs(east_score - west_score) > 20:
            penalty += w["penalties"]["conflict_ew"]

        fusion_score = max(0, min(100, fusion_raw + penalty + pc_offset))

        if miss == 0:
            fusion_score = min(100, fusion_score + w["bonuses"]["all_elements"])
        if bazi.get("elements", {}).get("strongest", bazi.get("day_master_element")) == bazi.get("day_master_element"):
            fusion_score = min(100, fusion_score + w["bonuses"]["strong_day_master"])

        # ---- Career intersection ----
        career_east = set(bazi.get("career_affinity", [])[:4])
        career_west = set(western.get("career_hints", [])[:4])
        career_overlap = list(career_east & career_west)
        career_all = list(career_east | career_west)

        # ---- Wealth ----
        wealth_level = bazi.get("wealth_potential", {}).get("level", "中")
        wealth_score = bazi.get("wealth_potential", {}).get("score", 0)

        # ---- Lifespan estimate (capped at 95) ----
        lifespan = 72
        el_counts = bazi.get("elements", {}).get("counts", {})
        miss = bazi.get("elements", {}).get("missing", [])
        dm = bazi.get("day_master_element", "")
        dm_strength = el_counts.get(dm, 0) if dm else 0
        lifespan -= len(miss) * 5
        if dm_strength >= 3:
            lifespan += 4
        elif dm_strength <= 1:
            lifespan -= 3
        controlled_by = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
        controller = controlled_by.get(dm, "")
        if controller and el_counts.get(controller, 0) >= 3:
            lifespan -= 5
        lifespan = max(40, min(95, lifespan))

        # === Yearly analysis (流年) for key ages ===
        year_timeline = self.yearly.analyze_life(bazi, y)
        high_risk_years = self.yearly.find_death_years(year_timeline)

        # === Qi Men Dun Jia birth timing ===
        qimen_birth = self.qimen.analyze_timing(y, m, d, h)

        # === Deep family analysis ===
        family_secret = self.life_collector.get_family_secret(name)
        family_deep = self.family_deep.analyze(bazi, y, gender, family_secret)

        # === Full life timeline if available ===
        life_timeline = self.life_collector.get_timeline(name)

        return {
            "fusion": {
                "score": round(fusion_score, 1),
                "east_score": round(east_score, 1),
                "west_score": round(west_score, 1),
                "num_score": round(num_score, 1),
                "stat_score": round(stat_score, 1),
                "name_score": round(name_score, 1),
                "name_element_influence": name_element_influence,
                "personal_code_offset": round(pc_offset, 2),
                "personal_code_desc": pc_desc,
                "east_weight": round(ew, 2),
                "west_weight": round(ww, 2),
                "num_weight": round(nw, 2),
                "stat_weight": round(sw, 2),
                "penalty": round(penalty, 1),
                "calibration_version": self.calibrator.params["calibration_count"],
                "accuracy": self.calibrator.params["accuracy"],
                "confidence_interval": self._confidence_interval(fusion_score, len(stat_wealth.get("distribution", {})) > 0),
            },
            "chinese": bazi,
            "western": western,
            "career": {
                "overlap": career_overlap,
                "all": career_all[:6],
                "east_affinity": bazi.get("career_affinity", [])[:4],
                "west_affinity": western.get("career_hints", [])[:4],
            },
            "wealth": {
                "level": wealth_level,
                "score": wealth_score,
            },
            "lifespan": {
                "estimate": round(lifespan),
                "base": w["lifespan_base"],
            },
            "statistical_evidence": {
                "career": stat_fusion.get("distribution", {}),
                "wealth": stat_wealth.get("distribution", {}),
                "lifespan": stat_lifespan.get("distribution", {}),
                "confidence": stat_wealth.get("confidence", 0),
                "total_patterns": self.pattern_db.stats()["total_patterns"],
                "total_cases": self.pattern_db.stats()["total_cases"],
            },
            "yearly": {
                "high_risk_years": high_risk_years[:5],
                "death_risk_at_70": None,
                "life_events": self._summarize_life_events(year_timeline),
            },
            "qimen": {
                "birth": {
                    "door": qimen_birth["door"]["name"],
                    "star": qimen_birth["star"]["name"],
                    "spirit": qimen_birth["spirit"]["name"],
                    "judgment": qimen_birth["overall"],
                },
                "risk_score": qimen_birth["risk_score"],
            },
            "family": family_deep,
            "life_timeline": life_timeline[:10] if life_timeline else [],
            "name": name,
            "birth": {"year": y, "month": m, "day": d, "hour": h},
        }

    def _summarize_life_events(self, timeline):
        """Summarize key event types across the life timeline."""
        types = {}
        for y in timeline:
            for e in y.get("events", []):
                if "意外" in e or "凶" in e or "血" in e:
                    types["accident"] = types.get("accident", 0) + 1
                if "喜" in e or "吉" in e:
                    types["fortune"] = types.get("fortune", 0) + 1
                if "官" in e:
                    types["legal"] = types.get("legal", 0) + 1
        return types

    def _score_bazi(self, bazi, w):
        """Score BaZi analysis quality."""
        el = bazi.get("elements", {})
        miss = len(el.get("missing", []))
        dm = bazi.get("day_master_element", "")
        dom = el.get("dominant", "")

        base = 60
        base -= miss * 8
        if dm == dom:
            base += w["bonuses"].get("strong_day_master", 8)
        if miss == 0:
            base += w["bonuses"].get("all_elements", 10)
        return max(10, min(100, base))

    def _score_western(self, western, w):
        """Score Western astrology analysis quality."""
        eb = western.get("element_balance", {})
        if not eb:
            return 50
        eb_int = {}
        for k, v in eb.items():
            try:
                eb_int[k] = int(str(v).replace("%", ""))
            except (ValueError, AttributeError):
                eb_int[k] = 0
        diversity = len([v for v in eb_int.values() if v > 5])
        base = 50 + diversity * 8
        return max(10, min(100, base))

    def _score_numerology(self, western, w):
        """Score numerology quality."""
        lp = western.get("life_path", 0)
        base = 50
        if 1 <= lp <= 9:
            base += 15
        return max(10, min(100, base))

    def _confidence_interval(self, score, has_stat_evidence):
        """Estimate confidence interval width."""
        if has_stat_evidence:
            return max(3, 15 - score * 0.1)
        return max(5, 20 - score * 0.1)

    def metadata(self):
        """Return system metadata for status display."""
        self.ensure_calibrated()
        st = self.pattern_db.stats()
        return {
            "version": 2,
            "calibration_count": self.calibrator.params["calibration_count"],
            "accuracy": self.calibrator.params["accuracy"],
            "pattern_count": st["total_patterns"],
            "case_count": st["total_cases"],
        }


def test():
    engine = FusionV2()
    figures = [
        ("爱因斯坦", 1879, 3, 14, 11, "男"),
        ("牛顿", 1643, 1, 4, 10, "男"),
        ("拿破仑", 1769, 8, 15, 12, "男"),
        ("达芬奇", 1452, 4, 15, 8, "男"),
    ]
    total = 0
    for name, y, m, d, h, g in figures:
        r = engine.analyze(y, m, d, h, name, g)
        s = r["fusion"]["score"]
        ci = r["fusion"]["confidence_interval"]
        acc = r["fusion"]["accuracy"]
        total += s
        print(f"{name}: fusion={s}±{ci:.0f}, accuracy={acc:.1f}%, "
              f"career_overlap={r['career']['overlap']}, "
              f"wealth={r['wealth']['level']}, "
              f"lifespan={r['lifespan']['estimate']}")
    print(f"\nAverage: {total/len(figures):.1f}/100")


if __name__ == "__main__":
    test()
