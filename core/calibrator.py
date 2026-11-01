"""Self-calibrating optimizer v2.
Goal: learn fusion weights that maximize accuracy against known historical outcomes.
Accuracy = how well predicted scores match known real-world outcomes across:
  - career domain (science/arts/politics/business/military)
  - wealth level (高/中/低)
  - lifespan (long/normal/short)
  - social mobility (高/中/低)

Uses Nelder-Mead style random search with simulated annealing."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, math, copy, random
from pathlib import Path
from datetime import date

class Calibrator:
    def __init__(self, param_path="data/calibrated_params.json"):
        self.param_path = Path(param_path)
        self.params = self._default_params()
        self._load()

    def _default_params(self):
        return {
            "weights": {"chinese": 1.0, "western": 1.0, "numerology": 1.0, "statistical": 1.0},
            "career_weights": {"east": 0.5, "west": 0.5},
            "wealth_weights": {"element": 0.4, "house": 0.3, "numerology": 0.3, "career": 1.0, "penalty": 1.0, "base_lifespan": 72},
            "lifespan_base": 75,
            "element_lifespan_bonus": {"金": 5, "木": 3, "水": 4, "火": 2, "土": 6},
            "penalties": {"missing_element": -8, "conflict_ew": -10, "weak_day_master": -12, "severe_conflict": -20},
            "bonuses": {"all_elements": 10, "strong_day_master": 8, "ew_agree": 12, "golden_mean": 15},
            "calibration_count": 0,
            "accuracy": 0.0,
        }

    def _load(self):
        if self.param_path.exists():
            with open(self.param_path, encoding="utf-8") as f:
                stored = json.load(f)
            for k in self.params:
                if k in stored:
                    self.params[k] = stored[k]

    def save(self):
        self.param_path.parent.mkdir(exist_ok=True)
        with open(self.param_path, "w", encoding="utf-8") as f:
            json.dump(self.params, f, ensure_ascii=False, indent=2)

    # === Domain classifiers ===

    CAREER_DOMAIN = {
        "物理学家": "科学", "科学家": "科学", "化学家": "科学", "生物学家": "科学",
        "数学家": "科学", "天文学家": "科学", "自然学家": "科学",
        "音乐家": "艺术", "作曲家": "艺术", "艺术家": "艺术", "画家": "艺术",
        "作家": "艺术", "剧作家": "艺术", "诗人": "艺术",
        "政治家": "政治", "革命家": "政治", "首相": "政治", "皇帝": "政治",
        "军事家": "军事",
        "医生": "医疗", "思想家": "学术", "发明家": "科技",
    }

    BAZI_CAREER_DOMAIN = {
        "科学": ["科研", "物理", "化学", "生物", "天文", "数学", "工程", "技术", "科技", "机械", "互联网"],
        "艺术": ["艺术", "音乐", "文学", "创作", "表演", "设计", "传媒", "出版", "写作", "电影", "文化", "体育", "旅游"],
        "政治": ["政治", "管理", "行政", "外交", "领导", "公共", "政府", "公务员"],
        "商业": ["商业", "金融", "经济", "贸易", "投资", "企业", "市场", "房地产", "创业", "人力资源", "物流", "销售"],
        "教育": ["教育", "学术", "研究", "教学", "培训", "顾问", "咨询", "心理咨询"],
        "医疗": ["医疗", "医药", "健康", "护理", "心理", "养生", "医疗外科"],
        "军事": ["军事", "国防", "安全", "战略", "指挥", "军警"],
        "法律": ["法律", "司法", "律师", "法官"],
        "建筑": ["建筑", "土木"],
        "环保": ["环保", "能源", "环境"],
        "农业": ["农业", "养殖", "种植"],
        "公益": ["慈善", "公益", "NGO"],
    }

    def _domain_career_map(self):
        """Map BaZi career affinity strings to domains."""
        m = {}
        for domain, keywords in self.BAZI_CAREER_DOMAIN.items():
            for kw in keywords:
                m[kw] = domain
        return m

    def _compute_domain_accuracy(self, predicted_careers, actual_careers):
        """Check if predicted career domain overlaps with actual domain."""
        if not actual_careers or not predicted_careers:
            return 0.5
        domain_map = self._domain_career_map()
        pred_domains = set()
        for c in predicted_careers:
            for kw, dom in domain_map.items():
                if kw in c:
                    pred_domains.add(dom)
        actual_domains = set()
        for c in actual_careers:
            act = self.CAREER_DOMAIN.get(c, c)
            actual_domains.add(act)
        if not pred_domains or not actual_domains:
            return 0.3
        overlap = len(pred_domains & actual_domains)
        union = len(pred_domains | actual_domains)
        return overlap / max(union, 1)

    def _compute_wealth_accuracy(self, predicted_level, actual_level):
        levels = {"低": 0, "中": 1, "高": 2}
        p = levels.get(predicted_level, 1)
        a = levels.get(actual_level, 1)
        return 1.0 - abs(p - a) / 2.0

    def _compute_lifespan_accuracy(self, predicted_age, actual_age):
        if not actual_age:
            return 0.5
        # Category accuracy: long(≥75) / normal(60-74) / short(<60)
        def cat(a):
            return 2 if a >= 75 else 1 if a >= 60 else 0
        return 1.0 if cat(predicted_age) == cat(actual_age) else 0.3

    def _compute_mobility_accuracy(self, predicted_mobility, actual_mobility):
        levels = {"低": 0, "中": 1, "高": 2}
        p = levels.get(predicted_mobility, 1)
        a = levels.get(actual_mobility, 1)
        return 1.0 - abs(p - a) / 2.0

    # === Prediction (lightweight: does not re-calc BaZi each time) ===

    def predict_outcomes(self, bazi_result, western_result, weights=None):
        """Predict outcomes from raw BaZi + Western results using given weights."""
        w = weights or self.params
        el = bazi_result.get("elements", {})
        miss = el.get("missing", [])
        dm = bazi_result.get("day_master_element", "")
        dom = el.get("dominant", "")

        # Base fusion score
        east_score = 60 - len(miss) * 8 + (10 if len(miss) == 0 else 0) + (8 if dm == dom else 0)
        west_eb = western_result.get("element_balance", {})
        west_eb_int = {}
        for k, v in west_eb.items():
            try:
                west_eb_int[k] = int(str(v).replace("%", ""))
            except (ValueError, AttributeError):
                west_eb_int[k] = 0
        west_diversity = len([v for v in west_eb_int.values() if v > 5])
        west_score = 50 + west_diversity * 8
        num_score = 65 if 1 <= western_result.get("life_path", 0) <= 9 else 45

        cw = w.get("weights", {})
        ew = cw.get("chinese", 1.0)
        ww = cw.get("western", 1.0)
        nw = cw.get("numerology", 1.0)
        total_w = ew + ww + nw

        fusion = (east_score * ew + west_score * ww + num_score * nw) / total_w
        penalty = len(miss) * w["penalties"]["missing_element"]
        if abs(east_score - west_score) > 20:
            penalty += w["penalties"]["conflict_ew"]
        if abs(east_score - west_score) > 35:
            penalty += w["penalties"]["severe_conflict"]
        fusion = max(0, min(100, fusion + penalty))
        if len(miss) == 0:
            fusion = min(100, fusion + w["bonuses"]["all_elements"])
        if dm == dom:
            fusion = min(100, fusion + w["bonuses"]["strong_day_master"])

        # Wealth: weight-dependent formula
        wealth = bazi_result.get("wealth_potential", {})
        wl_score = wealth.get("score", 50)
        el_counts = el.get("counts", {})
        wh = w.get("wealth_weights", {})
        wealth_el = wealth.get("wealth_element", "")
        wealth_el_strength = el_counts.get(wealth_el, 0) if wealth_el else 0
        has_business = any("金融" in c or "商业" in c or "投资" in c or "管理" in c
                          for c in bazi_result.get("career_affinity", []))
        wl_score += wealth_el_strength * wh.get("element", 0.4) * 15
        wl_score += (10 if has_business else 0) * wh.get("career", 1.0)
        wl_score -= len(miss) * 5 * wh.get("penalty", 1.0)
        wealth_level = "高" if wl_score >= 65 else "低" if wl_score <= 35 else "中"

        # Lifespan: weight-dependent formula
        lifespan = wh.get("base_lifespan", 72)
        dm_strength = el_counts.get(dm, 0) if dm else 0
        lifespan -= len(miss) * w["penalties"]["missing_element"] * 0.5
        if dm_strength >= 3:
            lifespan += w["bonuses"]["strong_day_master"] * 0.4
        elif dm_strength <= 1:
            lifespan -= w["bonuses"]["strong_day_master"] * 0.2
        controlled_by = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
        controller = controlled_by.get(dm, "")
        if controller and el_counts.get(controller, 0) >= 3:
            lifespan -= 5
        lifespan = max(40, min(95, lifespan))

        # Career (fixed - cannot calibrate)
        career_aff = bazi_result.get("career_affinity", [])
        career_hints = western_result.get("career_hints", [])

        # Social mobility
        dm_power = el.get("counts", {}).get(dm, 0) if dm else 0
        mobility = "高" if dm_power >= 3 else "中" if dm_power >= 2 else "低"

        return {
            "fusion_score": round(fusion, 1),
            "wealth_level": wealth_level,
            "lifespan": round(lifespan),
            "career_predicted": career_aff[:4] + career_hints[:4],
            "mobility": mobility,
        }

    def _compute_fusion_correlation(self, figures_with_scores, count):
        """Compute how well fusion_score correlates with actual life outcomes.
        Uses: wealth + lifespan + career_match as outcome proxy."""
        scores = [f["fusion_score"] for f in figures_with_scores]
        outcomes = []
        for f in figures_with_scores:
            w = {"低": 0, "中": 1, "高": 2}.get(f.get("actual_wealth_level", "中"), 1)
            l = f.get("lifespan", 70) / 20  # normalize
            c = f.get("career_match", 0.5)
            outcomes.append(w + l + c)
        if not scores or not outcomes:
            return 0.5
        # Simple rank correlation: if top half by score are also top half by outcome
        n = len(scores)
        paired = list(zip(scores, outcomes))
        paired.sort(key=lambda x: -x[0])
        top_half = paired[:n//2] if n > 1 else paired
        bottom_half = paired[n//2:] if n > 1 else []
        top_outcome = sum(o for _, o in top_half) / max(len(top_half), 1)
        bot_outcome = sum(o for _, o in bottom_half) / max(len(bottom_half), 1)
        # If top half has better outcomes, positive correlation
        if top_outcome > bot_outcome:
            ratio = (top_outcome - bot_outcome) / max(bot_outcome, 0.1)
            return min(1.0, 0.5 + ratio)
        else:
            return max(0.0, 0.5 - (bot_outcome - top_outcome) / max(bot_outcome, 0.1))

    def compute_accuracy(self, weights, validation_figures):
        """Compute overall accuracy across all known outcomes.
        Accepts pre-computed bazi_result/western_result in figures for speed."""
        career_acc = 0
        wealth_acc = 0
        lifespan_acc = 0
        mobility_acc = 0
        fusion_figures = []
        count = 0

        for fg in validation_figures:
            # Use pre-computed results if available
            bazi = fg.get("bazi_result")
            western = fg.get("western_result")

            if bazi is None or western is None:
                from core.bazi import BaziEngine
                from core.western import WesternEngine
                from datetime import date
                y = fg.get("birth_year")
                m = fg.get("birth_month")
                d = fg.get("birth_day")
                h = fg.get("birth_hour", 12)
                if not all([y, m, d]):
                    continue
                try:
                    bazi = BaziEngine().calculate(y, m, d, h)
                    western = WesternEngine().calculate_chart(date(y, m, d), h)
                except Exception:
                    continue

            pred = self.predict_outcomes(bazi, western, weights)

            actual_careers = fg.get("actual_careers", [])
            actual_wealth = fg.get("actual_wealth_level", "中")
            actual_lifespan = fg.get("lifespan", 0)
            actual_mobility = fg.get("family", {}).get("social_mobility", "中")

            ca = self._compute_domain_accuracy(pred["career_predicted"], actual_careers)
            wa = self._compute_wealth_accuracy(pred["wealth_level"], actual_wealth)
            la = self._compute_lifespan_accuracy(pred["lifespan"], actual_lifespan)
            ma = self._compute_mobility_accuracy(pred["mobility"], actual_mobility)

            career_acc += ca
            wealth_acc += wa
            lifespan_acc += la
            mobility_acc += ma
            fusion_figures.append({
                "fusion_score": pred["fusion_score"],
                "career_match": ca,
                "actual_wealth_level": actual_wealth,
                "lifespan": actual_lifespan,
            })
            count += 1

        if count == 0:
            return 0.0

        # Outcome accuracy: 50% weight on direct predictions, 50% on fusion correlation
        direct_acc = (career_acc + wealth_acc + lifespan_acc + mobility_acc) / (count * 4)
        fusion_corr = self._compute_fusion_correlation(fusion_figures, count)
        combined = (direct_acc * 0.5 + fusion_corr * 0.5) * 100
        return combined

    def calibrate(self, validation_figures, iterations=2000):
        """Evolutionary search: random mutations + periodic resets to escape plateaus."""
        print(f"[calibrator] v3 start: {len(validation_figures)} figures, {iterations} iters")

        best_params = None
        best_acc = 0.0
        history = []
        plateau_count = 0

        valid = [f for f in validation_figures if f.get("birth_year")]
        print(f"  usable: {len(valid)}/{len(validation_figures)}")

        # Precompute baseline accuracy with default params
        baseline = self.compute_accuracy(self._default_params(), valid)
        print(f"  baseline: {baseline:.1f}%")

        for i in range(iterations):
            trial = copy.deepcopy(self._default_params())

            if best_params and i > 50:
                base = best_params
                if plateau_count > 20:
                    # Escape plateau: large mutation
                    step = 2.0
                    reset_w = 0.3  # 30% chance to reset a param
                else:
                    step = 0.8 * (1 - i / iterations) ** 0.5 + 0.05
                    reset_w = 0.05
            else:
                base = trial
                step = 1.5
                reset_w = 0.1

            # Consider weighting dimensions differently
            for k in trial["weights"]:
                if random.random() < reset_w:
                    trial["weights"][k] = random.uniform(0.01, 5.0)
                else:
                    trial["weights"][k] = max(0.01, base["weights"].get(k, 1.0) + random.gauss(0, step))

            for k in trial["penalties"]:
                if random.random() < reset_w:
                    trial["penalties"][k] = random.uniform(-30, -1)
                else:
                    base_val = base["penalties"].get(k, -8)
                    trial["penalties"][k] = min(0, base_val + random.gauss(0, step * 8))

            for k in trial["bonuses"]:
                if random.random() < reset_w:
                    trial["bonuses"][k] = random.uniform(1, 30)
                else:
                    base_val = base["bonuses"].get(k, 8)
                    trial["bonuses"][k] = max(1, base_val + random.gauss(0, step * 5))

            acc = self.compute_accuracy(trial, valid)
            history.append(acc)

            if acc > best_acc:
                best_acc = acc
                best_params = trial
                plateau_count = 0
            else:
                plateau_count += 1

            if i % 200 == 0 and i > 0:
                recent = sum(history[-200:]) / len(history[-200:])
                print(f"  iter {i}: best_acc={best_acc:.1f}%, recent_avg={recent:.1f}%, plateau={plateau_count}")

        self.params = best_params or self._default_params()
        self.params["calibration_count"] += 1
        self.params["accuracy"] = round(best_acc, 2)
        self.save()

        improvement = best_acc - baseline
        print(f"[calibrator] Done. Baseline={baseline:.1f}%, Best={best_acc:.1f}%, Improvement=+{improvement:.1f}%")
        return {"accuracy": best_acc, "baseline": baseline, "improvement": improvement, "params": best_params}


def load_validation_figures(path="data/validation_enhanced.json"):
    """Load and enrich validation figures with birth data + known outcomes."""
    with open(path, encoding="utf-8") as f:
        v = json.load(f)
    figures = v.get("figures", [])

    REAL_CAREERS = {
        "Albert Einstein": ["物理学家", "科学家", "理论物理"],
        "Isaac Newton": ["物理学家", "数学家", "天文学家"],
        "Napoleon Bonaparte": ["军事家", "政治家", "皇帝"],
        "Wolfgang Mozart": ["音乐家", "作曲家"],
        "Ludwig Beethoven": ["音乐家", "作曲家"],
        "Charles Darwin": ["生物学家", "自然学家"],
        "Marie Curie": ["物理学家", "化学家"],
        "Winston Churchill": ["政治家", "作家", "首相"],
        "Leonardo da Vinci": ["艺术家", "发明家", "科学家"],
        "William Shakespeare": ["作家", "剧作家", "诗人"],
        "Mao Zedong": ["政治家", "革命家"],
        "Sun Yat-sen": ["政治家", "革命家", "医生"],
        "Lu Xun": ["作家", "思想家"],
    }
    REAL_WEALTH = {
        "Albert Einstein": "中", "Isaac Newton": "中", "Napoleon Bonaparte": "高",
        "Wolfgang Mozart": "中", "Ludwig Beethoven": "中", "Charles Darwin": "高",
        "Marie Curie": "中", "Winston Churchill": "高", "Leonardo da Vinci": "中",
        "William Shakespeare": "中", "Mao Zedong": "高", "Sun Yat-sen": "中", "Lu Xun": "中",
    }
    BIRTH = {
        "Albert Einstein": (1879, 3, 14, 11),
        "Isaac Newton": (1643, 1, 4, 10),
        "Napoleon Bonaparte": (1769, 8, 15, 12),
        "Wolfgang Mozart": (1756, 1, 27, 10),
        "Ludwig Beethoven": (1770, 12, 17, 8),
        "Charles Darwin": (1809, 2, 12, 9),
        "Marie Curie": (1867, 11, 7, 12),
        "Winston Churchill": (1874, 11, 30, 10),
        "Leonardo da Vinci": (1452, 4, 15, 8),
        "William Shakespeare": (1564, 4, 26, 12),
        "Mao Zedong": (1893, 12, 26, 10),
        "Sun Yat-sen": (1866, 11, 12, 11),
        "Lu Xun": (1881, 9, 25, 12),
    }

    for fg in figures:
        n = fg.get("name", "")
        fg["actual_careers"] = REAL_CAREERS.get(n, [])
        fg["actual_wealth_level"] = REAL_WEALTH.get(n, "中")
        if n in BIRTH:
            fg["birth_year"], fg["birth_month"], fg["birth_day"], fg["birth_hour"] = BIRTH[n]
    return figures


if __name__ == "__main__":
    figures = load_validation_figures()
    c = Calibrator()
    result = c.calibrate(figures, iterations=4000)
    print(f"\nFinal accuracy: {result['accuracy']:.1f}%")
    print(f"Optimal weights: {json.dumps(c.params['weights'], ensure_ascii=False)}")
