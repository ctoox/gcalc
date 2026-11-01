"""Comprehensive Life Report — year-by-year from birth to death.
Covers career, wealth, love, health, family, major events.
Calibratable: user confirms past events, system adjusts future predictions."""
import sys, os, math, json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi import BaziEngine
from core.western import WesternEngine
from core.yearly import YearlyEngine, year_gan_zhi, TIAN_GAN, DI_ZHI, WU_XING_GAN, WU_XING_ZHI
from core.qimen import QiMenEngine
from core.fusion_v2 import FusionV2
from core.family_deep import FamilyDeepAnalyzer
from datetime import date

# ── Constants ──

SHICHEN_MAP = {23:"子",1:"丑",3:"寅",5:"卯",7:"辰",9:"巳",11:"午",13:"未",15:"申",17:"酉",19:"戌",21:"亥"}
GENDER_MAP = {"男": "male", "女": "female"}

# 大运 顺逆
YIN_YANG_GAN = {"甲":"阳","丙":"阳","戊":"阳","庚":"阳","壬":"阳",
                "乙":"阴","丁":"阴","己":"阴","辛":"阴","癸":"阴"}

# Life domains
DOMAINS = ["career", "wealth", "love", "health", "family", "social"]

DOMAIN_LABELS = {
    "career": "事业", "wealth": "财富", "love": "感情",
    "health": "健康", "family": "家庭", "social": "人际"
}

# Year element tendencies
TENDENCY_MAP = {
    "甲": {"career": "开创", "wealth": "正财", "love": "桃花淡", "health": "肝胆需养"},
    "乙": {"career": "协作", "wealth": "偏财", "love": "人缘佳", "health": "注意筋骨"},
    "丙": {"career": "表现", "wealth": "暴发", "love": "热情", "health": "心血管注意"},
    "丁": {"career": "精细", "wealth": "细水长流", "love": "含蓄", "health": "眼目保养"},
    "戊": {"career": "稳重", "wealth": "积累", "love": "平淡", "health": "脾胃调理"},
    "己": {"career": "规划", "wealth": "储蓄", "love": "务实", "health": "皮肤注意"},
    "庚": {"career": "变革", "wealth": "大刀阔斧", "love": "果断", "health": "呼吸系统"},
    "辛": {"career": "转型", "wealth": "偏财机遇", "love": "细腻", "health": "肺经保养"},
    "壬": {"career": "扩张", "wealth": "大进大出", "love": "浪漫", "health": "肾水调理"},
    "癸": {"career": "内收", "wealth": "隐秘财", "love": "敏感", "health": "泌尿系统"},
}

ZHI_TENDENCY = {
    "子":{"career":"变动","wealth":"暗财","love":"桃花","health":"水过剩","family":"家庭变动"},
    "丑":{"career":"积累","wealth":"正财稳","love":"平淡","health":"土湿","family":"长辈助力"},
    "寅":{"career":"突破","wealth":"偏财","love":"热情","health":"肝火旺","family":"迁居"},
    "卯":{"career":"发展","wealth":"正财","love":"桃花旺","health":"注意肝胆","family":"朋友助力"},
    "辰":{"career":"转折","wealth":"守财","love":"低调","health":"脾胃问题","family":"家庭稳定"},
    "巳":{"career":"加速","wealth":"暴发","love":"激情","health":"心血管","family":"社交活跃"},
    "午":{"career":"高峰","wealth":"旺财","love":"热烈","health":"心火旺","family":"喜庆"},
    "未":{"career":"调整","wealth":"稳中求进","love":"温和","health":"脾胃调理","family":"家庭和谐"},
    "申":{"career":"变革","wealth":"偏财机遇","love":"追求","health":"肺经","family":"位置变动"},
    "酉":{"career":"精致","wealth":"积蓄","love":"含蓄","health":"保养","family":"稳定"},
    "戌":{"career":"收官","wealth":"暗财","love":"孤独","health":"注意意外","family":"长辈健康"},
    "亥":{"career":"酝酿","wealth":"暗流","love":"暧昧","health":"肾水调理","family":"家庭秘密"},
}

# Major event trigger patterns
EVENT_PATTERNS = {
    "marriage": {
        "name": "婚缘",
        "triggers": {
            "spirits": ["红鸾"],
            "conflicts": [],
            "age_range": (22, 40),
        },
        "desc": "红鸾星动之年，婚缘机会",
    },
    "job_change": {
        "name": "事业变动",
        "triggers": {
            "spirits": ["驿马"],
            "conflicts": ["日犯岁君", "岁君冲年"],
            "age_range": (20, 60),
        },
        "desc": "驿马星动或日犯岁君，事业变动年",
    },
    "accident": {
        "name": "意外风险",
        "triggers": {
            "spirits": ["灾煞", "血刃", "天刑", "劫煞"],
            "conflicts": ["日犯岁君", "岁伤日干"],
            "age_range": (0, 100),
        },
        "desc": "凶煞临门之年，意外风险高",
    },
    "wealth_loss": {
        "name": "破财",
        "triggers": {
            "spirits": ["大耗", "劫煞"],
            "conflicts": [],
            "age_range": (0, 100),
        },
        "desc": "大耗劫煞之年，投资需谨慎",
    },
    "family_change": {
        "name": "家庭变动",
        "triggers": {
            "spirits": ["丧门", "吊客"],
            "conflicts": ["岁君冲年"],
            "age_range": (0, 100),
        },
        "desc": "丧吊临门或冲年柱，家庭重大变化",
    },
    "move": {
        "name": "迁居远行",
        "triggers": {
            "spirits": ["驿马"],
            "conflicts": [],
            "age_range": (0, 100),
        },
        "desc": "驿马星动，迁居或远行",
    },
}


def calc_da_yun(bazi_result, gender, birth_year):
    """Calculate 大运 (Major Fortune) periods.
    Returns list of (start_age, start_year, gan_zhi, description)."""
    bazi_str = bazi_result.get("bazi", "")
    pillars = bazi_str.split() if bazi_str else ["", "", "", ""]
    year_pillar = pillars[0] if len(pillars) > 0 else ""
    year_gan = year_pillar[0] if len(year_pillar) > 0 else "甲"
    year_zhi = year_pillar[1] if len(year_pillar) > 1 else "子"

    # 阳男阴女顺行，阴男阳女逆行
    gan_yinyang = YIN_YANG_GAN.get(year_gan, "阳")
    is_male = (gender == "男" or gender == "male")
    shun_ni = (gan_yinyang == "阳" and is_male) or (gan_yinyang == "阴" and not is_male)
    direction = "顺" if shun_ni else "逆"

    zhi_idx = DI_ZHI.index(year_zhi) if year_zhi in DI_ZHI else 0

    da_yun = []
    # 大运每10年一换
    for decade in range(0, 80, 10):
        if shun_ni:
            yun_idx = (zhi_idx + decade // 10 + 1) % 12
        else:
            yun_idx = (zhi_idx - (decade // 10 + 1)) % 12
        yun_zhi = DI_ZHI[yun_idx]
        yun_gan = TIAN_GAN[(TIAN_GAN.index(year_gan) + (decade // 10 + 1)) % 10]
        da_yun.append({
            "大运": f"{yun_gan}{yun_zhi}",
            "start_age": decade,
            "start_year": birth_year + decade,
            "direction": direction,
            "element_gan": WU_XING_GAN.get(yun_gan, ""),
            "element_zhi": WU_XING_ZHI.get(yun_zhi, ""),
        })
    return da_yun


def calc_shen_sha_detail(year_zhi, day_zhi, day_gan, month_zhi):
    """Detailed 神煞 calculation with more spirits."""
    shensha = []
    # 桃花
    TAO_HUA = {"寅":"卯","午":"卯","戌":"卯","巳":"午","酉":"午","丑":"午",
               "申":"子","子":"子","辰":"子","亥":"酉","卯":"酉","未":"酉"}
    # 驿马
    YI_MA = {"寅":"申","午":"申","戌":"申","巳":"亥","酉":"亥","丑":"亥",
             "申":"寅","子":"寅","辰":"寅","亥":"巳","卯":"巳","未":"巳"}
    # 华盖
    HUA_GAI = {"寅":"戌","午":"戌","戌":"戌","巳":"丑","酉":"丑","丑":"丑",
               "申":"辰","子":"辰","辰":"辰","亥":"未","卯":"未","未":"未"}
    # 孤辰寡宿
    GU_CHEN = {"寅":"巳","午":"巳","戌":"巳","巳":"申","酉":"申","丑":"申",
               "申":"亥","子":"亥","辰":"亥","亥":"寅","卯":"寅","未":"寅"}

    taohua_zhi = TAO_HUA.get(day_zhi, "")
    yima_zhi = YI_MA.get(year_zhi, "")
    huagai_zhi = HUA_GAI.get(year_zhi, "")
    guchen_zhi = GU_CHEN.get(year_zhi, "")

    if year_zhi == taohua_zhi:
        shensha.append({"name": "桃花", "type": "吉", "meaning": "人缘佳,异性缘旺"})
    if year_zhi == yima_zhi:
        shensha.append({"name": "驿马", "type": "吉", "meaning": "动中求财,升迁变动"})
    if year_zhi == huagai_zhi:
        shensha.append({"name": "华盖", "type": "平", "meaning": "孤独清高,才艺天赋"})
    if year_zhi == guchen_zhi:
        shensha.append({"name": "孤辰", "type": "凶", "meaning": "孤独寂寞,亲缘淡薄"})

    # 天乙贵人
    TIAN_YI = {"甲":"丑未","乙":"子申","丙":"酉亥","丁":"酉亥","戊":"丑未",
               "己":"子申","庚":"丑未","辛":"午寅","壬":"卯巳","癸":"卯巳"}
    yigui_str = TIAN_YI.get(day_gan, "")
    if year_zhi in yigui_str:
        shensha.append({"name": "天乙贵人", "type": "吉", "meaning": "贵人相助,转危为安"})

    # 文昌
    WEN_CHANG = {"甲":"巳","乙":"午","丙":"申","丁":"酉","戊":"申","己":"酉","庚":"亥","辛":"子","壬":"寅","癸":"卯"}
    wenchang_zhi = WEN_CHANG.get(day_gan, "")
    if year_zhi == wenchang_zhi and wenchang_zhi:
        shensha.append({"name": "文昌", "type": "吉", "meaning": "学业进步,文思敏捷"})

    return shensha


class LifeReport:
    def __init__(self):
        self.be = BaziEngine()
        self.we = WesternEngine()
        self.ye = YearlyEngine()
        self.qm = QiMenEngine()
        self.fusion = FusionV2()
        self.family = FamilyDeepAnalyzer()

    def generate(self, year, month, day, hour, name="", gender="男", calibration_data=None, personal_code=""):
        """Generate comprehensive life report.
        calibration_data: list of {year, event, confirmed} for past event matching.
        personal_code: unique per-user code for identical-birth disambiguation."""
        # Base calculations
        bazi = self.be.calculate(year, month, day, hour)
        western = self.we.calculate_chart(date(year, month, day), hour)
        fusion_result = self.fusion.analyze(year, month, day, hour, name, gender, personal_code=personal_code)
        family_deep = self.family.analyze(bazi, {})
        fs = fusion_result["fusion"]

        bazi_str = bazi.get("bazi", "")
        pillars = bazi_str.split() if bazi_str else ["", "", "", ""]
        day_gan = pillars[2][0] if len(pillars) > 2 and len(pillars[2]) > 0 else ""
        day_zhi = pillars[2][1] if len(pillars) > 2 and len(pillars[2]) > 1 else ""
        year_zhi = pillars[0][1] if len(pillars) > 0 and len(pillars[0]) > 1 else ""
        month_zhi = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) > 1 else ""

        # 大运
        da_yun = calc_da_yun(bazi, gender, year)

        # Current age
        current_year = date.today().year
        age_now = current_year - year

        # Full yearly timeline
        timeline = []
        death_est = fusion_result["lifespan"]["estimate"]
        end_year = max(current_year + 50, year + death_est)

        for y in range(year, end_year + 1):
            age = y - year + 1
            if age > death_est + 10:
                break

            # Get base yearly analysis
            yg, yz = year_gan_zhi(y)
            base_year = self.ye.analyze_year(bazi, y, age)

            # Enhanced per-domain analysis
            tendencies = self._domain_tendencies(yg, yz, bazi, age)

            # Major events detection
            events = self._detect_events(base_year, yg, yz, day_gan, day_zhi, year_zhi, month_zhi, age)

            # Domain scores
            scores = self._domain_scores(base_year, yg, yz, day_gan, bazi, age)

            # Deep Bazi interaction for this year
            bazi_interaction = self._year_bazi_interaction(yg, yz, pillars, bazi)

            year_data = {
                "year": y,
                "age": age,
                "gan_zhi": f"{yg}{yz}",
                "is_past": y <= current_year,
                "is_current": y == current_year,
                "is_future": y > current_year,
                "incalendar": y == current_year,
                "da_yun": self._current_da_yun(da_yun, age),
                "conflicts": base_year["conflicts"],
                "harmonies": base_year["harmonies"],
                "spirits_good": base_year["spirits_good"],
                "spirits_bad": base_year["spirits_bad"],
                "accident_risk": base_year["accident_risk"],
                "shensha_detail": calc_shen_sha_detail(yz, day_zhi, day_gan, month_zhi),
                "tendencies": tendencies,
                "events": events,
                "scores": scores,
                "qimen": self._qimen_annual(y, month, day, hour),
                "bazi_interaction": bazi_interaction,
            }
            timeline.append(year_data)

        # Major event summary (past)
        past_events = [t for t in timeline if t["is_past"] and t["events"]]
        major_past = self._summarize_major_events(past_events)

        # Future highlights
        future_events = [t for t in timeline if t["is_future"] and t["events"]]
        major_future = self._summarize_major_events(future_events)

        # Complete past timeline (every single year from birth to present)
        past_timeline_full = [
            t for t in timeline if (t["is_past"] or t["is_current"])
        ]

        # Future 10-year deep analysis
        future_10_deep = []
        for t in timeline:
            if t["is_future"] and len(future_10_deep) < 10:
                future_10_deep.append(t)

        # Inject calibration data into timeline for display
        if calibration_data:
            for ud in calibration_data:
                ud_year = ud.get("year")
                for ty in timeline:
                    if ty["year"] == ud_year:
                        ty["calibration_override"] = ud.get("event", "")
                        break

        # Calibration
        calibration = self._calibrate(timeline, calibration_data)

        # Assemble report
        report = {
            "metadata": {
                "name": name,
                "birth": f"{year}年{month}月{day}日 {hour}时",
                "gender": gender,
                "age": age_now,
                "current_year": current_year,
                "generated": str(date.today()),
            },
            "bazi_summary": {
                "八字": bazi_str,
                "日主": bazi.get("day_master_element", ""),
                "五行": {
                    "旺": bazi.get("elements", {}).get("dominant", ""),
                    "缺": bazi.get("elements", {}).get("missing", []),
                    "分布": bazi.get("elements", {}).get("counts", {}),
                },
                "藏干": bazi.get("hidden_stems", []),
                "纳音": bazi.get("nayin", ""),
                "性格": bazi.get("personality", ""),
            },
            "fusion": {
                "score": fs["score"],
                "east": fs["east_score"],
                "west": fs["west_score"],
                "num": fs["num_score"],
                "stat": fs.get("stat_score", 0),
                "accuracy": fs["accuracy"],
            },
            "da_yun": da_yun,
            "career": {
                "affinity": bazi.get("career_affinity", []),
                "western_hints": western.get("career_hints", []),
                "overlap": fusion_result["career"].get("overlap", []),
            },
            "wealth": fusion_result["wealth"],
            "lifespan_estimate": death_est,
            "family": family_deep,
            "western": {
                "sun": western.get("sun_sign", ""),
                "moon": western.get("moon_sign", ""),
                "rising": western.get("rising_sign", ""),
                "element_balance": western.get("element_balance", {}),
            },
            "yearly_timeline": timeline,
            "major_past_events": major_past,
            "major_future_events": major_future,
            "past_timeline_complete": past_timeline_full,
            "future_10_deep": future_10_deep,
            "future_10_forecast": self._summarize_future_forecast(future_10_deep, bazi),
            "calibration": calibration,
            "confidence": self._report_confidence(fs, calibration),
        }

        return report

    def _domain_tendencies(self, yg, yz, bazi_result, age):
        """Compute tendencies for each life domain in a given year."""
        dm = bazi_result.get("day_master_element", "")
        miss = bazi_result.get("elements", {}).get("missing", [])

        gan_tend = TENDENCY_MAP.get(yg, {})
        zhi_tend = ZHI_TENDENCY.get(yz, {})

        tendencies = {}
        for domain in DOMAINS:
            parts = []
            if domain in gan_tend:
                parts.append(gan_tend[domain])
            if domain in zhi_tend:
                parts.append(zhi_tend[domain])

            # Element-based adjustments
            yg_el = WU_XING_GAN.get(yg, "")
            yz_el = WU_XING_ZHI.get(yz, "")
            ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

            if domain == "career" and yg_el:
                if sheng.get(yg_el) == dm:
                    parts.append("流年助日主")
                elif ke.get(yg_el) == dm:
                    parts.append("流年克日主")

            if domain == "health" and yg_el and miss:
                if yg_el in miss:
                    parts.append(f"{yg_el}补缺利好")
                if yz_el in miss:
                    parts.append(f"{yz_el}补缺")

            tendencies[domain] = "，".join(parts) if parts else "平稳"
            tendencies[DOMAIN_LABELS[domain]] = tendencies.pop(domain)

        return tendencies

    def _detect_events(self, base_year, yg, yz, day_gan, day_zhi, year_zhi, month_zhi, age):
        """Detect meaningful life events for this year."""
        events = []
        base_events = base_year.get("events", [])

        for ev in base_events:
            events.append({
                "type": "general",
                "text": ev,
                "severity": "high" if "大凶" in ev else "medium",
            })

        # Pattern-based event detection
        for pat_name, pat in EVENT_PATTERNS.items():
            triggers = pat["triggers"]
            score = 0

            # Check spirits
            for s in triggers.get("spirits", []):
                if s in base_year["spirits_bad"] or s in base_year["spirits_good"]:
                    score += 2

            # Check conflicts
            for c in triggers.get("conflicts", []):
                if c in base_year["conflicts"]:
                    score += 3

            # Check age range
            age_range = triggers.get("age_range", (0, 100))
            if age < age_range[0] or age > age_range[1]:
                score = 0

            if score >= 2:
                events.append({
                    "type": pat_name,
                    "text": pat["desc"],
                    "score": score,
                    "severity": "high" if score >= 4 else "medium",
                })

        # Specific checks
        # 桃花年
        TAO_HUA = {"寅":"卯","午":"卯","戌":"卯","巳":"午","酉":"午","丑":"午",
                   "申":"子","子":"子","辰":"子","亥":"酉","卯":"酉","未":"酉"}
        if TAO_HUA.get(day_zhi) == yz:
            events.append({"type": "love", "text": "桃花年: 异性缘旺盛", "severity": "medium"})

        # 红鸾 + 桃花 = 婚缘
        if "红鸾" in base_year["spirits_good"] and TAO_HUA.get(day_zhi) == yz:
            events.append({"type": "marriage", "text": "婚缘年: 红鸾桃花齐动", "severity": "high"})

        # 天克地冲
        if "日犯岁君" in base_year["conflicts"] and "岁伤日干" in base_year["conflicts"]:
            events.append({"type": "disaster", "text": "天克地冲: 本年大凶,谨慎行事", "severity": "critical"})

        return events

    def _domain_scores(self, base_year, yg, yz, day_gan, bazi_result, age):
        """Score each domain 0-100 for the year."""
        dm = bazi_result.get("day_master_element", "")
        scores = {}

        # Career: based on harmony/conflict with day master
        career = 60
        for c in base_year["conflicts"]:
            if "岁" in c:
                career -= 10
        if "驿马" in base_year["spirits_good"]:
            career += 15
        if "天德" in base_year["spirits_good"]:
            career += 10
        if "文昌" in base_year["spirits_good"]:
            career += 10
        scores["career"] = max(0, min(100, career))

        # Wealth
        wealth = 55
        if "大耗" in base_year["spirits_bad"]:
            wealth -= 20
        if "劫煞" in base_year["spirits_bad"]:
            wealth -= 10
        if "天乙" in base_year["spirits_good"]:
            wealth += 10
        scores["wealth"] = max(0, min(100, wealth))

        # Love
        love = 50
        if "红鸾" in base_year["spirits_good"]:
            love += 25
        if "桃花" in [s.get("name") for s in calc_shen_sha_detail(yz, "", "", "")]:
            love += 15
        if "孤辰" in [s.get("name") for s in calc_shen_sha_detail(yz, "", "", "")]:
            love -= 20
        scores["love"] = max(0, min(100, love))

        # Health
        health = 70
        health -= base_year["accident_risk"] * 0.5
        if "丧门" in base_year["spirits_bad"] or "吊客" in base_year["spirits_bad"]:
            health -= 15
        scores["health"] = max(0, min(100, health))

        # Family
        family = 60
        if "岁君冲年" in base_year["conflicts"]:
            family -= 15
        if "六合" in str(base_year.get("harmonies", [])):
            family += 10
        scores["family"] = max(0, min(100, family))

        # Social
        social = 55
        if "驿马" in base_year["spirits_good"]:
            social += 15
        if "桃花" in [s.get("name") for s in calc_shen_sha_detail(yz, "", "", "")]:
            social += 10
        scores["social"] = max(0, min(100, social))

        return scores

    def _current_da_yun(self, da_yun_list, age):
        """Find which 大运 the person is in at a given age."""
        for dy in reversed(da_yun_list):
            if age >= dy["start_age"]:
                return dy
        return da_yun_list[0] if da_yun_list else {}

    def _qimen_annual(self, year, month, day, hour):
        """Quick qimen for the year (uses mid-year date)."""
        try:
            qm = self.qm.calculate(year, 6, 15, hour)
            return {
                "door": qm.get("door", {}).get("name", ""),
                "star": qm.get("star", {}).get("name", ""),
                "spirit": qm.get("spirit", {}).get("name", ""),
                "risk": qm.get("risk_score", 0),
            }
        except Exception:
            return {"door": "", "star": "", "spirit": "", "risk": 0}

    def _year_bazi_interaction(self, yg, yz, pillars, bazi_result):
        """Deep Bazi interaction analysis for a given year.
        Shows how the year pillar interacts with each of the 4 birth pillars."""
        if len(pillars) < 4:
            return {"summary": "未知"}
        result = {}
        pillar_names = ["年柱", "月柱", "日柱", "时柱"]
        na_yin_map = {
            "甲子": "海中金", "乙丑": "海中金", "丙寅": "炉中火", "丁卯": "炉中火",
            "戊辰": "大林木", "己巳": "大林木", "庚午": "路旁土", "辛未": "路旁土",
            "壬申": "剑锋金", "癸酉": "剑锋金", "甲戌": "山头火", "乙亥": "山头火",
            "丙子": "涧下水", "丁丑": "涧下水", "戊寅": "城头土", "己卯": "城头土",
            "庚辰": "白蜡金", "辛巳": "白蜡金", "壬午": "杨柳木", "癸未": "杨柳木",
            "甲申": "泉中水", "乙酉": "泉中水", "丙戌": "屋上土", "丁亥": "屋上土",
            "戊子": "霹雳火", "己丑": "霹雳火", "庚寅": "松柏木", "辛卯": "松柏木",
            "壬辰": "长流水", "癸巳": "长流水", "甲午": "沙中金", "乙未": "沙中金",
            "丙申": "山下火", "丁酉": "山下火", "戊戌": "平地木", "己亥": "平地木",
            "庚子": "壁上土", "辛丑": "壁上土", "壬寅": "金箔金", "癸卯": "金箔金",
            "甲辰": "覆灯火", "乙巳": "覆灯火", "丙午": "天河水", "丁未": "天河水",
            "戊申": "大驿土", "己酉": "大驿土", "庚戌": "钗钏金", "辛亥": "钗钏金",
            "壬子": "桑柘木", "癸丑": "桑柘木", "甲寅": "大溪水", "乙卯": "大溪水",
            "丙辰": "沙中土", "丁巳": "沙中土", "戊午": "天上火", "己未": "天上火",
            "庚申": "石榴木", "辛酉": "石榴木", "壬戌": "大海水", "癸亥": "大海水",
        }
        year_na_yin = na_yin_map.get(f"{yg}{yz}", "")
        year_el_gan = WU_XING_GAN.get(yg, "")
        year_el_zhi = WU_XING_ZHI.get(yz, "")

        for i, pillar in enumerate(pillars):
            if len(pillar) < 2:
                continue
            p_gan = pillar[0]
            p_zhi = pillar[1]
            p_na_yin = na_yin_map.get(pillar, "")
            # 生克关系: 流年天干 vs 各柱天干
            p_gan_el = WU_XING_GAN.get(p_gan, "")
            ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
            if p_gan_el and year_el_gan:
                if sheng.get(year_el_gan) == p_gan_el:
                    relation = "生"
                elif ke.get(year_el_gan) == p_gan_el:
                    relation = "克"
                elif year_el_gan == p_gan_el:
                    relation = "同"
                elif sheng.get(p_gan_el) == year_el_gan:
                    relation = "被生"
                elif ke.get(p_gan_el) == year_el_gan:
                    relation = "被克"
                else:
                    relation = "平"
            else:
                relation = "平"

            # 纳音生克
            na_yin_relation = ""
            if p_na_yin and year_na_yin:
                na_el_map = {"金": "金", "木": "木", "水": "水", "火": "火", "土": "土"}
                py_el = ""
                yy_el = ""
                for el_name in ["金","木","水","火","土"]:
                    if el_name in p_na_yin:
                        py_el = el_name
                    if el_name in year_na_yin:
                        yy_el = el_name
                if py_el and yy_el:
                    if sheng.get(yy_el) == py_el:
                        na_yin_relation = "生"
                    elif ke.get(yy_el) == py_el:
                        na_yin_relation = "克"
                    elif yy_el == py_el:
                        na_yin_relation = "同"

            result[pillar_names[i]] = {
                "柱": pillar,
                "流年天干关系": relation,
                "纳音": p_na_yin,
                "纳音生克": na_yin_relation,
            }

        result["纳音"] = year_na_yin
        result["summary"] = ""
        # Generate a short summary
        if "克" in str(result) or "被克" in str(result):
            result["summary"] = "流年克柱，压力挑战"
        if "同" in str(result):
            result["summary"] = result.get("summary", "") + "，柱年比和"
        if not result["summary"]:
            result["summary"] = "流年平和"
        return result

    def _summarize_major_events(self, timeline_years):
        """Extract major events from timeline."""
        major = []
        for ty in timeline_years:
            for ev in ty["events"]:
                if ev.get("severity") in ("high", "critical"):
                    major.append({
                        "year": ty["year"],
                        "age": ty["age"],
                        "gan_zhi": ty["gan_zhi"],
                        "type": ev["type"],
                        "text": ev["text"],
                        "severity": ev["severity"],
                        "da_yun": ty.get("da_yun", {}).get("大运", ""),
                    })
        return major

    def _calibrate(self, timeline, user_data):
        """Calibrate predictions against user-provided life events."""
        if not user_data:
            return {
                "calibrated": False,
                "accuracy": None,
                "matched_events": 0,
                "total_events": 0,
                "message": "暂无校准数据，提供你的过去经历可提升精度",
            }
        matched = 0
        for ud in user_data:
            ud_year = ud.get("year")
            ud_event = ud.get("event", "").lower()
            for ty in timeline:
                if ty["year"] != ud_year:
                    continue
                for ev in ty["events"]:
                    if any(kw in ev["text"].lower() for kw in ud_event.split()):
                        matched += 1
                        break
        total = len(user_data)
        accuracy = matched / total if total > 0 else 0
        return {
            "calibrated": True,
            "accuracy": round(accuracy * 100, 1),
            "matched_events": matched,
            "total_events": total,
            "message": f"已匹配{matched}/{total}个事件,系统校准中",
        }

    def _summarize_future_forecast(self, future_10, bazi_result):
        """Generate summarized text analysis for the next 10 years.
        Returns list of {year, gan_zhi, summary, focus_domain, advice}."""
        result = []
        dm = bazi_result.get("day_master_element", "")
        miss = bazi_result.get("elements", {}).get("missing", [])
        for ty in future_10:
            yr = ty["year"]
            yg = ty["gan_zhi"][0] if ty["gan_zhi"] else ""
            yz = ty["gan_zhi"][1] if len(ty["gan_zhi"]) > 1 else ""
            yg_el = WU_XING_GAN.get(yg, "")
            yz_el = WU_XING_ZHI.get(yz, "")
            ke = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

            # Determine focus domain
            focus = "事业"
            max_score = 0
            for domain, label in [("career", "事业"), ("wealth", "财富"), ("love", "感情"),
                                  ("health", "健康"), ("family", "家庭")]:
                sc = ty.get("scores", {}).get(domain, 0)
                if sc > max_score:
                    max_score = sc
                    focus = label

            # Generate advice
            advice_parts = []
            if yg_el and dm:
                if sheng.get(yg_el) == dm:
                    advice_parts.append(f"{yg}生助日主{dm}，运势得力")
                elif ke.get(yg_el) == dm:
                    advice_parts.append(f"{yg}克日主{dm}，注意压力")
            if "大耗" in ty.get("spirits_bad", []):
                advice_parts.append("谨防破财")
            if "红鸾" in ty.get("spirits_good", []):
                advice_parts.append("婚缘机会")
            if "驿马" in ty.get("spirits_good", []):
                advice_parts.append("动中求财")
            if "文昌" in ty.get("spirits_good", []):
                advice_parts.append("学习/考证吉年")
            if ty.get("accident_risk", 0) > 30:
                advice_parts.append("注意意外伤灾")
            if ty.get("conflicts"):
                advice_parts.append("流年犯冲，谨慎行事")

            future_type = "上升期" if max_score >= 70 else "平稳期" if max_score >= 50 else "调整期"
            if "换大运" in str(ty.get("da_yun", {})):
                future_type = "转折期"

            result.append({
                "year": yr,
                "age": ty["age"],
                "gan_zhi": ty["gan_zhi"],
                "type": future_type,
                "focus_domain": focus,
                "career_score": ty.get("scores", {}).get("career", 0),
                "wealth_score": ty.get("scores", {}).get("wealth", 0),
                "love_score": ty.get("scores", {}).get("love", 0),
                "health_score": ty.get("scores", {}).get("health", 0),
                "family_score": ty.get("scores", {}).get("family", 0),
                "bad_spirits": ty.get("spirits_bad", []),
                "good_spirits": ty.get("spirits_good", []),
                "advice": "，".join(advice_parts) if advice_parts else "平稳度过",
                "da_yun": ty.get("da_yun", {}).get("大运", ""),
                "da_yun_change": ty.get("da_yun", {}).get("start_age") == ty["age"],
            })
        return result

    def _report_confidence(self, fs, calibration):
        """Overall confidence score for the report."""
        base = fs["accuracy"]  # 0-100
        if calibration.get("calibrated"):
            cal_acc = calibration.get("accuracy", 0)
            return round(base * 0.6 + cal_acc * 0.4, 1)
        return round(base, 1)

    def to_text(self, report):
        """Render report as plain text (for display)."""
        lines = []
        m = report["metadata"]
        b = report["bazi_summary"]
        f = report["fusion"]
        now = m["current_year"]

        lines.append(f"【{m['name']} 综合命理报告】")
        lines.append(f"出生: {m['birth']} | 性别: {m['gender']} | 现年: {m['age']}岁")
        lines.append(f"八字: {b['八字']} | 日主: {b['日主']} | 旺: {b['五行']['旺']} | 缺: {'/'.join(b['五行']['缺']) if b['五行']['缺'] else '俱全'}")
        lines.append(f"五行分布: 金{b['五行']['分布'].get('金',0)} 木{b['五行']['分布'].get('木',0)} 水{b['五行']['分布'].get('水',0)} 火{b['五行']['分布'].get('火',0)} 土{b['五行']['分布'].get('土',0)}")
        lines.append(f"性格: {b['性格']}")
        lines.append(f"综合评分: {f['score']}/100 (东{f['east']:.0f}/西{f['west']:.0f}/数{f['num']:.0f}/统{f['stat']:.0f})")
        lines.append(f"系统精度: {f['accuracy']}%")
        lines.append("")

        # 大运
        lines.append("【大运走势】")
        for dy in report["da_yun"]:
            marker = " ← 当前" if dy["start_age"] <= m["age"] < dy["start_age"] + 10 else ""
            lines.append(f"  {dy['start_age']}岁({dy['start_year']})起: {dy['大运']} ({dy['direction']}){marker}")
        lines.append("")

        # Career
        c = report["career"]
        lines.append("【事业倾向】")
        lines.append(f"  八字: {'/'.join(c['affinity'])}")
        lines.append(f"  占星: {'/'.join(c['western_hints'])}")
        lines.append(f"  交集: {'/'.join(c['overlap']) if c['overlap'] else '待发掘'}")
        lines.append("")

        # ── COMPLETE PAST: every year from birth → present ──
        lines.append("=" * 72)
        lines.append(f"【完整人生回顾 · {m['birth'][:4]}年至今({m['age']}岁)】")
        lines.append("=" * 72)
        past_all = report.get("past_timeline_complete", [])
        for ty in past_all:
            yr = ty["year"]
            ag = ty["age"]
            gz = ty["gan_zhi"]
            s = ty["scores"]
            dy = ty.get("da_yun", {}).get("大运", "")
            bad = ", ".join(ty.get("spirits_bad", [])) or "无"
            good = ", ".join(ty.get("spirits_good", [])) or "无"

            lines.append(f"")
            lines.append(f"── {yr}年({ag}岁) {gz} [大运{dy}] ──")
            lines.append(f"  事{s['career']} 财{s['wealth']} 爱{s['love']} 健{s['health']} 家{s['family']}")
            if bad != "无":
                lines.append(f"  凶煞: {bad}")
            if good != "无":
                lines.append(f"  吉神: {good}")
            for ev in ty.get("events", []):
                sev = "★" if ev.get("severity") in ("high", "critical") else "▸"
                lines.append(f"  {sev} {ev['text']}")
            if ty.get("calibration_override"):
                lines.append(f"  ✓ 实际: {ty['calibration_override']}")
            bi = ty.get("bazi_interaction", {})
            if bi.get("summary"):
                lines.append(f"  {bi['summary']}")
        lines.append("")

        # ── FUTURE 10 YEAR DEEP FORECAST ──
        lines.append("=" * 72)
        lines.append(f"【未来十年深度推算 · {now+1}年-{now+10}年】")
        lines.append("=" * 72)

        # Show the structured forecast first
        forecast = report.get("future_10_forecast", [])
        lines.append(f"")
        lines.append(f"{'年份':>4} {'年龄':>4} {'干支':>4} {'类型':<6} {'重点':<6} {'事':>3} {'财':>3} {'爱':>3} {'健':>3} {'家':>3} {'建议'}")
        lines.append("-" * 72)
        for fc in forecast:
            dy_mark = "★" if fc.get("da_yun_change") else " "
            lines.append(f"{fc['year']:>4} {fc['age']:>4} {fc['gan_zhi']:>4} {fc['type']:<6} {fc['focus_domain']:<6} {fc['career_score']:>3} {fc['wealth_score']:>3} {fc['love_score']:>3} {fc['health_score']:>3} {fc['family_score']:>3} {fc['advice']}")

        # Deep detail for each future year
        for ty in report.get("future_10_deep", []):
            yr = ty["year"]
            ag = ty["age"]
            gz = ty["gan_zhi"]
            s = ty["scores"]
            dy = ty.get("da_yun", {})

            lines.append(f"")
            lines.append(f"── {yr}年({ag}岁) {gz} {'★换大运' if dy.get('start_age') == ag else ''} ──")
            lines.append(f"  八字流年交互:")
            bi = ty.get("bazi_interaction", {})
            for pillar_name, interaction in bi.items():
                if isinstance(interaction, dict):
                    lines.append(f"    {pillar_name}: {interaction['柱']} → {interaction['流年天干关系']} (纳音{interaction.get('纳音','')}{' '+interaction.get('纳音生克','') if interaction.get('纳音生克') else ''})")
            lines.append(f"  评分: 事{s['career']} 财{s['wealth']} 爱{s['love']} 健{s['health']} 家{s['family']}")
            if ty.get("spirits_bad"):
                lines.append(f"  凶煞: {', '.join(ty['spirits_bad'])}")
            if ty.get("spirits_good"):
                lines.append(f"  吉神: {', '.join(ty['spirits_good'])}")
            if ty.get("accident_risk", 0) > 0:
                lines.append(f"  意外风险: {ty['accident_risk']}%")
            for ev in ty.get("events", []):
                sev = "★" if ev.get("severity") in ("high", "critical") else "▸"
                lines.append(f"  {sev} {ev['text']}")
            # Matching forecast advice
            for fc in forecast:
                if fc["year"] == yr and fc.get("advice"):
                    lines.append(f"  → {fc['advice']}")
        lines.append("")

        # Future major events summary
        lines.append("【未来重大事件】")
        if report["major_future_events"]:
            for ev in report["major_future_events"][:15]:
                lines.append(f"  {ev['year']}年({ev['age']}岁) [{ev['severity']}] {ev['text']}")
        lines.append("")

        # LLM enhancement if present
        if report.get("_llm_advice"):
            lines.append("【LLM 综合建议】")
            lines.append(f"  {report['_llm_advice']}")
            lines.append("")
        if report.get("_llm_career"):
            lines.append("【LLM 事业分析】")
            lines.append(f"  {report['_llm_career']}")
            lines.append("")

        # Calibration
        lines.append(f"【系统报告置信度】: {report['confidence']}%")
        if report.get("calibration", {}).get("calibrated"):
            cal = report["calibration"]
            lines.append(f"校准匹配: {cal['matched_events']}/{cal['total_events']} ({cal['accuracy']}%)")
        else:
            lines.append("提示: 提供你的过去经历可提升预测精度")

        return "\n".join(lines)


def generate_text_report(year, month, day, hour, name, gender="男",
                          calibration_data=None, personal_code="", llm=False):
    """One-shot: generate a full life report and return both dict and text.
    If llm=True, also run LLM enhancement (requires Groq API key + proxy)."""
    lr = LifeReport()
    report = lr.generate(year, month, day, hour, name, gender,
                          calibration_data=calibration_data, personal_code=personal_code)
    if llm:
        from core.llm_enhancer import enhance_report
        report = enhance_report(report)
    text = lr.to_text(report)
    return report, text
