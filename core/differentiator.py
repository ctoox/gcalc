"""命理区分器 — Destiny Differentiator.
Handles: same birth time different fate, twins, same name, location correction.
核心原则: 八字定先天70%, 后天环境+个人选择30%."""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bazi import BaziEngine
from datetime import datetime, timedelta, date
from math import floor

# Chinese city coordinates (lat, lng)
CITIES = {
    "北京": (39.9, 116.4), "上海": (31.2, 121.5), "广州": (23.1, 113.3),
    "深圳": (22.5, 114.1), "成都": (30.6, 104.1), "杭州": (30.3, 120.2),
    "武汉": (30.6, 114.3), "南京": (32.1, 118.8), "重庆": (29.6, 106.5),
    "西安": (34.3, 108.9), "长沙": (28.2, 112.9), "青岛": (36.1, 120.4),
    "大连": (38.9, 121.6), "厦门": (24.5, 118.1), "沈阳": (41.8, 123.4),
    "济南": (36.7, 117.0), "哈尔滨": (45.8, 126.7), "昆明": (25.0, 102.7),
    "郑州": (34.8, 113.7), "合肥": (31.9, 117.3), "南昌": (28.7, 115.9),
    "太原": (37.9, 112.5), "石家庄": (38.0, 114.5), "南宁": (22.8, 108.4),
    "贵阳": (26.6, 106.7), "兰州": (36.0, 103.8), "西宁": (36.6, 101.8),
    "银川": (38.5, 106.2), "拉萨": (29.7, 91.1), "乌鲁木齐": (43.8, 87.6),
    "台北": (25.0, 121.5), "香港": (22.3, 114.2), "澳门": (22.2, 113.5),
    # US cities
    "New York": (40.7, -74.0), "Washington DC": (38.9, -77.0),
    "Los Angeles": (34.1, -118.2), "Chicago": (41.9, -87.6),
    "Houston": (29.8, -95.4), "Dallas": (32.8, -96.8),
    "San Francisco": (37.8, -122.4), "Boston": (42.4, -71.1),
}

# Stroke-to-element mapping (simplified Kangxi radical count)
# Using simplified Wuxing classification of stroke counts
STROKE_ELEMENT = {
    "1": "木", "2": "木", "3": "火", "4": "火", "5": "土",
    "6": "土", "7": "金", "8": "金", "9": "水", "0": "水",
}

# Common Chinese surnames with stroke counts
SURNAMES_STROKES = {
    "王": 4, "李": 7, "张": 7, "刘": 6, "陈": 7, "杨": 7,
    "赵": 9, "黄": 11, "周": 8, "吴": 7, "徐": 10, "孙": 6,
    "胡": 9, "朱": 6, "高": 10, "林": 8, "何": 7, "郭": 10,
    "马": 10, "罗": 8, "梁": 11, "宋": 7, "郑": 8, "谢": 12,
    "韩": 12, "唐": 10, "冯": 5, "于": 3, "董": 12, "萧": 11,
    "程": 12, "曹": 11, "袁": 10, "邓": 4, "许": 6, "傅": 12,
    "沈": 7, "曾": 12, "彭": 12, "吕": 6, "苏": 7, "卢": 5,
    "蒋": 14, "蔡": 14, "贾": 13, "丁": 2, "魏": 17, "薛": 16,
    "叶": 12, "阎": 11, "余": 7, "潘": 15, "杜": 7, "戴": 17,
    "夏": 10, "钟": 9, "田": 5, "任": 6, "姜": 9, "范": 8,
    "方": 4, "石": 5, "姚": 9, "谭": 14, "廖": 14, "邹": 7,
    "熊": 14, "金": 8, "陆": 7, "郝": 9, "孔": 4, "白": 5,
    "崔": 11, "康": 11, "毛": 4, "邱": 7, "秦": 10, "江": 6,
}


class DestinyDifferentiator:
    def __init__(self):
        self.bazi = BaziEngine()

    def get_solar_time(self, year, month, day, hour, minute, city):
        """Convert Beijing/local time to true solar time.
        Returns adjusted hour for BaZi calculation."""
        if city not in CITIES:
            return hour, minute, 0  # No adjustment

        _, lng = CITIES[city]
        # China uses UTC+8 (120°E)
        std_meridian = 120.0
        # 4 minutes per degree
        offset_minutes = (lng - std_meridian) * 4
        # Add equation of time (simplified, ignoring seasonal variation)
        total_minutes = hour * 60 + minute + offset_minutes
        adj_hour = total_minutes / 60.0
        adj_h = int(adj_hour)
        adj_m = int((adj_hour - adj_h) * 60)
        # Clamp
        adj_h = max(0, min(23, adj_h))
        return adj_h, adj_m, round(offset_minutes)

    def _minute_to_shichen(self, hour, minute):
        """Convert exact time to 时辰 (2-hour period).
        Even minute differences can change 时柱."""
        # 23:00-00:59 = 子, 01:00-02:59 = 丑, etc.
        total_min = hour * 60 + minute
        # 子时 starts at 23:00 (1380 min)
        idx = ((total_min + 60) // 120) % 12  # shift by 1 hour for 子时 starting at 23:00
        branches = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
        return branches[idx]

    def differentiate_twins(self, year, month, day, hour, minute1, minute2,
                           city="北京", gender1="男", gender2="女",
                           birth_order=1, total_twins=2):
        """Analyze how twins with same date but different minutes differ.
        minute1/minute2: birth minutes for each twin.
        birth_order: 1=先出生, 2=后出生
        """
        adj_h1, adj_m1, offset = self.get_solar_time(year, month, day, hour, minute1, city)
        adj_h2, adj_m2, _ = self.get_solar_time(year, month, day, hour, minute2, city)

        # Check if they fall in different 时辰
        shichen1 = self._minute_to_shichen(adj_h1, adj_m1)
        shichen2 = self._minute_to_shichen(adj_h2, adj_m2)
        same_shichen = shichen1 == shichen2

        # Calculate BaZi for each
        bazi1 = self.bazi.calculate(year, month, day, adj_h1)
        bazi2 = self.bazi.calculate(year, month, day, adj_h2)

        # 大运 direction depends on gender + 年干阴阳
        year_gan = bazi1.get("bazi", "").split()[0][0] if bazi1.get("bazi") else "甲"
        yang_gan = {"甲","丙","戊","庚","壬"}
        year_yang = year_gan in yang_gan

        # Male + 阳年 = 顺排, Female + 阴年 = 顺排
        dayun1_forward = (gender1 == "男" and year_yang) or (gender1 == "女" and not year_yang)
        dayun2_forward = (gender2 == "男" and year_yang) or (gender2 == "女" and not year_yang)

        # Birth order effect: 先出生 = 年柱更旺, 后出生 = 月柱更旺
        order_effect = {1: "先出生: 继承祖业,年柱影响力更大",
                        2: "后出生: 自力更生,月柱影响力更大",
                        3: "中间出生: 兄弟宫复杂",
                        4: "末子: 父母宠爱,晚年得力"}.get(birth_order, "出生顺序影响")

        differences = []
        if not same_shichen:
            differences.append(f"时辰不同: {shichen1} vs {shichen2} {'→ 命局不同' if bazi1.get('bazi')!=bazi2.get('bazi') else ''}")
        if gender1 != gender2:
            differences.append(f"性别不同: 大运{'顺' if dayun1_forward else '逆'}排 vs {'顺' if dayun2_forward else '逆'}排")
        if birth_order:
            differences.append(order_effect)

        result = {
            "twin_a": {
                "birth": f"{year}-{month:02d}-{day:02d} {adj_h1:02d}:{adj_m1:02d}",
                "shi_chen": shichen1,
                "bazi": bazi1.get("bazi", ""),
                "day_master": bazi1.get("day_master_element", ""),
                "gender": gender1,
                "dayun_direction": "顺排" if dayun1_forward else "逆排",
                "qi_yun_age": bazi1.get("fortune_cycles", {}).get("start_age", 0),
            },
            "twin_b": {
                "birth": f"{year}-{month:02d}-{day:02d} {adj_h2:02d}:{adj_m2:02d}",
                "shi_chen": shichen2,
                "bazi": bazi2.get("bazi", ""),
                "day_master": bazi2.get("day_master_element", ""),
                "gender": gender2,
                "dayun_direction": "顺排" if dayun2_forward else "逆排",
                "qi_yun_age": bazi2.get("fortune_cycles", {}).get("start_age", 0),
            },
            "same_shichen": same_shichen,
            "same_bazi": bazi1.get("bazi") == bazi2.get("bazi"),
            "solar_time_offset": offset,
            "city": city,
            "differences": differences,
            "key_factors": self._twin_key_factors(gender1, gender2, birth_order, same_shichen),
        }
        return result

    def differentiate_same_name(self, name, ref_name="",
                                birth_data=None, ref_birth=None):
        """Analyze two people with the same name (or same birth time).
        birth_data: dict with {year, month, day, hour, minute, city, gender}
        ref_birth: reference person's birth data
        """
        if not birth_data or not ref_birth:
            return {"error": "需要两组出生数据"}

        # True solar time correction
        city1 = birth_data.get("city", "北京")
        city2 = ref_birth.get("city", "北京")
        y1, m1, d1 = birth_data["year"], birth_data["month"], birth_data["day"]
        y2, m2, d2 = ref_birth["year"], ref_birth["month"], ref_birth["day"]
        h1 = birth_data.get("hour", 12)
        h2 = ref_birth.get("hour", 12)
        min1 = birth_data.get("minute", 0)
        min2 = ref_birth.get("minute", 0)
        g1 = birth_data.get("gender", "男")
        g2 = ref_birth.get("gender", "男")

        adj_h1, adj_m1, off1 = self.get_solar_time(y1, m1, d1, h1, min1, city1)
        adj_h2, adj_m2, off2 = self.get_solar_time(y2, m2, d2, h2, min2, city2)

        b1 = self.bazi.calculate(y1, m1, d1, adj_h1)
        b2 = self.bazi.calculate(y2, m2, d2, adj_h2)

        # Name element analysis
        name_el1 = self.get_name_element(name, g1)
        name_el2 = self.get_name_element(ref_name or name, g2)

        dm1 = b1.get("day_master_element", "")
        dm2 = b2.get("day_master_element", "")
        miss1 = set(b1.get("elements", {}).get("missing", []))
        miss2 = set(b2.get("elements", {}).get("missing", []))

        # Name remedies missing element?
        remedy1 = "补" + "".join(miss1 & name_el1["elements"]) if name_el1["elements"] & miss1 else ""
        remedy2 = "补" + "".join(miss2 & name_el2["elements"]) if name_el2["elements"] & miss2 else ""

        return {
            "person_a": {
                "name": name,
                "birth": f"{y1}-{m1:02d}-{d1:02d} {h1:02d}:{min1:02d}",
                "solar_time": f"{adj_h1:02d}:{adj_m1:02d} (修正{off1}分钟)",
                "city": city1,
                "gender": g1,
                "bazi": b1.get("bazi", ""),
                "day_master": dm1,
                "missing": "".join(miss1) if miss1 else "俱全",
                "name_element": "".join(name_el1["elements"]) if name_el1["elements"] else "无用神",
                "name_remedy": remedy1 or "无特殊补救",
            },
            "person_b": {
                "name": ref_name or name,
                "birth": f"{y2}-{m2:02d}-{d2:02d} {h2:02d}:{min2:02d}",
                "solar_time": f"{adj_h2:02d}:{adj_m2:02d} (修正{off2}分钟)",
                "city": city2,
                "gender": g2,
                "bazi": b2.get("bazi", ""),
                "day_master": dm2,
                "missing": "".join(miss2) if miss2 else "俱全",
                "name_element": "".join(name_el2["elements"]) if name_el2["elements"] else "无用神",
                "name_remedy": remedy2 or "无特殊补救",
            },
            "same_bazi": b1.get("bazi") == b2.get("bazi"),
            "same_day_master": dm1 == dm2,
            "differ_by": self._differentiation_factors(
                b1, b2, g1, g2, city1, city2,
                name_el1, name_el2, birth_data, ref_birth
            ),
        }

    def get_name_element(self, name, gender="男"):
        """Analyze the Wu Xing element of a Chinese name."""
        elements = set()
        element_counts = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        total_strokes = 0

        for char in name:
            # Try lookup, else use simple stroke → element mapping
            if char in SURNAMES_STROKES:
                strokes = SURNAMES_STROKES[char]
            else:
                # Default: use Unicode CJK unified ideograph block estimate
                cp = ord(char)
                if 0x4E00 <= cp <= 0x9FFF:
                    strokes = ((cp - 0x4E00) % 10) + 1
                else:
                    strokes = 5  # default

            total_strokes += strokes
            last_digit = str(strokes)[-1]
            el = STROKE_ELEMENT.get(last_digit, "土")
            elements.add(el)
            element_counts[el] = element_counts.get(el, 0) + 1

        dominant = max(element_counts, key=element_counts.get) if any(element_counts.values()) else "土"
        return {
            "total_strokes": total_strokes,
            "elements": elements,
            "dominant": dominant,
            "counts": element_counts,
        }

    def _differentiation_factors(self, b1, b2, g1, g2, c1, c2, ne1, ne2, bd1, bd2):
        """List all factors that differentiate two people with same/similar charts."""
        factors = []

        # Location
        if c1 != c2:
            factors.append(f"出生地不同: {c1} vs {c2} → 地理风水异")

        # Gender
        if g1 != g2:
            yg = b1.get("bazi", "")[0] if b1.get("bazi") else "甲"
            yang_gan = {"甲","丙","戊","庚","壬"}
            yy = yg in yang_gan
            d1 = (g1=="男" and yy) or (g1=="女" and not yy)
            d2 = (g2=="男" and yy) or (g2=="女" and not yy)
            factors.append(f"性别不同 → 大运{'顺' if d1 else '逆'}排 vs {'顺' if d2 else '逆'}排")

        # Name element
        if ne1["dominant"] != ne2["dominant"]:
            factors.append(f"姓名用神不同: {ne1['dominant']} vs {ne2['dominant']} → 后天补救异")

        # Missing element remedy
        m1 = set(b1.get("elements", {}).get("missing", []))
        m2 = set(b2.get("elements", {}).get("missing", []))
        if ne1["elements"] & m1:
            factors.append(f"姓名{''.join(ne1['elements']&m1)}补{name}所缺(若有)")
        if ne2["elements"] & m2:
            factors.append(f"姓名{''.join(ne2['elements']&m2)}补另者所缺(若有)")

        # Age difference
        if bd1 and bd2 and bd1.get("year") != bd2.get("year"):
            factors.append(f"出生年份不同 → 时代背景迥异")

        factors.append("先天八字定七分,后天环境+个人选择定三分")
        return factors

    def _twin_key_factors(self, g1, g2, order, same_shichen):
        """Key factors that differentiate twins."""
        factors = []
        if g1 != g2:
            factors.append("性别不同 → 大运顺逆相反,人生轨迹分叉")
        if not same_shichen:
            factors.append("时辰不同 → 时柱异,晚年/子女运不同")
        if order == 1:
            factors.append("先出生: 年柱祖荫更强,责任感更强")
        else:
            factors.append("后出生: 月柱兄弟宫影响,独立性更强")
        factors.append("即使命局相同,选择不同→命运不同(量子叠加态)")
        return factors

    def destiny_fork_report(self, year, month, day, hour, minute,
                            city="北京", gender="男", name=""):
        """Generate a report showing how destiny would fork based on
        different choices/locations/names for the same birth time.
        Addresses: '如果我叫肯尼迪,也在那天出生,我的人生会一样吗?'"""
        adj_h, adj_m, offset = self.get_solar_time(year, month, day, hour, minute, city)
        bazi = self.bazi.calculate(year, month, day, adj_h)
        shichen = self._minute_to_shichen(adj_h, adj_m)
        dm = bazi.get("day_master_element", "")
        miss = bazi.get("elements", {}).get("missing", [])

        name_el = self.get_name_element(name, gender) if name else None

        # Same birth time scenarios
        scenarios = []
        # Scenario 1: Different city
        for alt_city in ["上海", "广州", "成都", "New York", "Los Angeles"]:
            if alt_city != city:
                alt_h, alt_m, alt_off = self.get_solar_time(year, month, day, hour, minute, alt_city)
                alt_shichen = self._minute_to_shichen(alt_h, alt_m)
                alt_bazi = self.bazi.calculate(year, month, day, alt_h)
                diff = "时柱不同" if alt_bazi.get("bazi") != bazi.get("bazi") else "时柱同"
                scenarios.append({
                    "scenario": f"生在{alt_city}",
                    "solar_time": f"{alt_h:02d}:{alt_m:02d} (修正{alt_off}分)",
                    "shi_chen": alt_shichen,
                    "bazi": alt_bazi.get("bazi", ""),
                    "difference": diff,
                })

        return {
            "query": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} {city} {gender} {name or ''}",
            "base_bazi": {
                "bazi": bazi.get("bazi", ""),
                "shi_chen": shichen,
                "day_master": dm,
                "missing": "".join(miss) if miss else "俱全",
                "solar_time": f"{adj_h:02d}:{adj_m:02d}",
                "solar_offset": offset,
            },
            "name_element": {
                "total_strokes": name_el["total_strokes"] if name_el else 0,
                "dominant_el": name_el["dominant"] if name_el else "?",
                "counts": name_el["counts"] if name_el else {},
            } if name_el else None,
            "key_insight": (
                f"先天同一八字({bazi.get('bazi','')}),但: "
                f"出生地→时柱可异,性别→大运顺逆可异,"
                f"姓名→补救五行可异,时代→社会环境迥异,"
                f"个人选择→后天三分定乾坤. "
                f"双胞胎尚且不同命,何况同名同时不同地不同时代."
            ),
            "nature_vs_nurture": {
                "先天八字": "70%",
                "后天环境": "15%",
                "个人选择": "15%",
            },
            "same_time_celebrities": self._find_same_time_celebrities(year, month, day, hour, city),
        }

    def _find_same_time_celebrities(self, year, month, day, hour, city):
        """Find famous people born at approximately the same time."""
        from datetime import date
        celebs = []
        # Known celebrities with same month+day
        famous = {
            (3, 14): ["Albert Einstein(1879)", "Stephen Hawking(2018去世)"],
            (1, 4): ["Isaac Newton(1643)", "Louis Braille(1809)"],
            (8, 15): ["Napoleon Bonaparte(1769)"],
            (2, 12): ["Abraham Lincoln(1809)", "Charles Darwin(1809)"],
            (11, 30): ["Winston Churchill(1874)", "Mark Twain(1835)"],
            (12, 26): ["Mao Zedong(1893)"],
            (5, 29): ["John F. Kennedy(1917)"],
            (7, 1): ["Princess Diana(1961)"],
        }
        key = (month, day)
        if key in famous:
            for c in famous[key]:
                celebs.append(c)
        return celebs
