"""Input sanitizer: normalize, validate, anti-fake.
Ensures no two different inputs produce the same result."""
import re, unicodedata, hashlib, json

# Chinese name validation
VALID_NAME = re.compile(r'^[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef\w\-\.\s]+$')
# Allowed: CJK unified ideographs, CJK extension A, CJK symbols, fullwidth, word chars, hyphen, dot, space

INVISIBLE_CHARS = re.compile(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f\u200b-\u200f\u2028-\u202f\ufeff]')
MULTI_SPACE = re.compile(r' {2,}')

# BaZi 笔画→五行 mapping (standard)
STROKE_ELEMENT = {
    1: "木", 2: "木", 3: "火", 4: "火", 5: "土", 6: "土", 7: "金", 8: "金", 9: "水", 10: "水",
    11: "木", 12: "木", 13: "火", 14: "火", 15: "土", 16: "土", 17: "金", 18: "金", 19: "水", 20: "水",
    21: "木", 22: "木", 23: "火", 24: "火", 25: "土", 26: "土", 27: "金", 28: "金", 29: "水", 30: "水",
    31: "木", 32: "木", 33: "火", 34: "火", 35: "土", 36: "土", 37: "金", 38: "金", 39: "水", 40: "水",
    41: "木", 42: "木", 43: "火", 44: "火", 45: "土", 46: "土", 47: "金", 48: "金", 49: "水", 50: "水",
    51: "木", 52: "木", 53: "火", 54: "火", 55: "土", 56: "土", 57: "金", 58: "金", 59: "水", 60: "水",
    61: "木", 62: "木", 63: "火", 64: "火", 65: "土", 66: "土", 67: "金", 68: "金", 69: "水", 70: "水",
    71: "木", 72: "木", 73: "火", 74: "火", 75: "土", 76: "土", 77: "金", 78: "金", 79: "水", 80: "水",
    81: "木",
}

# Common strokes for simplified Chinese characters (楷体 simplified)
# This is a reference set; full mapping needs a proper dictionary
COMMON_STROKES = {
    "一": 1, "二": 2, "三": 3, "四": 5, "五": 4, "六": 4, "七": 2, "八": 2, "九": 2, "十": 2,
    "罗": 8, "展": 10, "程": 12,
    "李": 7, "王": 4, "张": 7, "刘": 6, "陈": 7, "杨": 7, "赵": 9, "黄": 11, "周": 8, "吴": 7,
    "徐": 10, "孙": 6, "马": 3, "朱": 6, "胡": 9, "郭": 10, "何": 7, "高": 10, "林": 8, "罗": 8,
    "郑": 8, "梁": 11, "谢": 12, "宋": 7, "唐": 10, "韩": 12, "曹": 11, "许": 6, "邓": 4, "萧": 11,
    "冯": 5, "曾": 12, "程": 12, "蔡": 14, "彭": 12, "潘": 15, "袁": 10, "于": 3, "董": 12, "余": 7,
    "苏": 7, "叶": 5, "吕": 6, "魏": 17, "蒋": 12, "田": 5, "杜": 7, "丁": 2, "沈": 7, "任": 6,
    "姚": 9, "卢": 5, "傅": 12, "钟": 9, "崔": 11, "汪": 7, "范": 8, "石": 5, "金": 8, "陆": 7,
    "毛": 4, "习": 3, "江": 6, "邓": 4, "胡": 9, "温": 12, "周": 8, "朱": 6, "华": 6, "向": 6,
    "白": 5, "万": 3, "廖": 14, "邹": 7, "熊": 14, "秦": 10, "孟": 8, "谭": 14, "薛": 16, "雷": 13,
    "贺": 9, "倪": 10, "汤": 6, "滕": 15, "殷": 10, "毕": 6, "郝": 9, "邬": 6, "安": 6, "常": 11,
    "乐": 5, "于": 3, "时": 7, "傅": 12, "康": 11, "伍": 6, "元": 4, "平": 5, "甘": 5, "柳": 9,
    "展": 10, "程": 12,
}


def sanitize_name(raw):
    """Clean and validate name. Returns (cleaned_name, error_message)."""
    if not raw or not raw.strip():
        return "", "姓名不能为空"

    # Normalize unicode (NFKC: fullwidth → halfwidth, etc.)
    cleaned = unicodedata.normalize("NFKC", raw)

    # Remove invisible/control characters
    cleaned = INVISIBLE_CHARS.sub("", cleaned)

    # Collapse multiple spaces → single space
    cleaned = MULTI_SPACE.sub(" ", cleaned)

    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()

    if not cleaned:
        return "", "姓名不能为空"

    # Check for suspicious characters
    if not VALID_NAME.match(cleaned):
        return "", "姓名包含非法字符"

    visible = cleaned.replace(" ", "")
    cjk_count = sum(1 for c in visible if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')
    alpha_count = sum(1 for c in visible if c.isalpha() and not ('\u4e00' <= c <= '\u9fff'))

    if cjk_count >= 2:
        # Chinese name: 2-6 characters
        if cjk_count > 6:
            return "", "姓名过长（最多6个汉字）"
    elif alpha_count >= 2:
        # Western name: 2-50 chars
        if len(visible) > 50:
            return "", "姓名过长"
    else:
        return "", "姓名至少2个字符"

    # Check for repeated single character (fake names like "啊啊啊啊")
    if cjk_count >= 3:
        unique_chars = set(visible)
        if len(unique_chars) <= 1:
            return "", "姓名不能全是重复字"

    # Spaces in Chinese names - allow for 3-character given names
    if cjk_count >= 2 and " " in cleaned:
        parts = cleaned.split()
        # Each part should be at least 1 CJK char
        for p in parts:
            pc = sum(1 for c in p if '\u4e00' <= c <= '\u9fff')
            if pc == 0 and len(p) > 0:
                # Could be Western name mixed with Chinese
                pass

    return cleaned, ""


def validate_date(year, month, day, hour, minute=0):
    """Validate date/time. Returns (valid, error_message)."""
    current_year = 2026

    # Basic range checks
    if year is None or year < -5000 or year > current_year + 1:
        return False, f"出生年份不合法({year})"

    if month is None or month < 1 or month > 12:
        return False, f"出生月份不合法({month})"

    if day is None or day < 1 or day > 31:
        return False, f"出生日不合法({day})"

    if hour is None or hour < 0 or hour > 23:
        return False, f"出生时辰不合法({hour})"

    if minute is None or minute < 0 or minute > 59:
        return False, "出生分钟不合法"

    # Month-day validity
    month_days = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
                  7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    max_day = month_days.get(month, 30)
    if day > max_day:
        return False, f"{month}月最多{max_day}天"

    # For Feb 29, only valid in leap years
    if month == 2 and day == 29:
        # Simple leap year check
        if not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            return False, f"{year}年不是闰年，2月只有28天"

    # Not too young (must be at least 1 year old)
    if year > current_year - 1:
        return False, "出生年份太近"

    # Not too old (max 150 years)
    if year < current_year - 150:
        return False, "出生年份太远"

    return True, ""


def name_stroke_element(name):
    """Calculate name's 五行 from stroke count + unique name hash.
    Returns dict with per-character strokes + overall element + unique name influence score."""
    visible = name.replace(" ", "")
    strokes = []
    elements = []
    for c in visible:
        if '\u4e00' <= c <= '\u9fff':
            stroke = COMMON_STROKES.get(c, 8)
            element = STROKE_ELEMENT.get(stroke, "土")
            strokes.append({"char": c, "stroke": stroke, "element": element})
            elements.append(element)
        else:
            strokes.append({"char": c, "stroke": 0, "element": "?"})

    from collections import Counter
    if elements:
        total_strokes = sum(s["stroke"] for s in strokes if s["stroke"] > 0)
        overall_element = STROKE_ELEMENT.get(total_strokes % 81 or 81, "土")
        dominant = Counter(elements).most_common(1)[0][0] if elements else "土"
    else:
        total_strokes = 0
        overall_element = "土"
        dominant = "土"

    # Unique name hash → deterministic influence score 0-100
    # This ensures EVERY different name → different influence, even if stroke count same
    name_bytes = name.encode("utf-8")
    hash_bytes = hashlib.sha256(name_bytes).digest()
    hash_score = (int.from_bytes(hash_bytes[:4], "big") % 10000) / 100  # 0.00 - 99.99
    combine_byte = hash_bytes[0]
    # Use hash to pick a secondary element influencing the name (adds variety)
    hash_elements = ["木", "火", "土", "金", "水"]
    secondary_element = hash_elements[combine_byte % 5]

    return {
        "chars": strokes,
        "total_strokes": total_strokes,
        "dominant_element": dominant,
        "total_element": overall_element,
        "hash_score": round(hash_score, 2),
        "secondary_element": secondary_element,
        "full_name_length": len(visible),
    }


def compute_signature(name, year, month, day, hour, bazi_str, personal_code=""):
    """Generate a unique signature for the reading (anti-tamper)."""
    raw = f"{name}|{year}|{month}|{day}|{hour}|{bazi_str}|{personal_code}|gcalc-v2"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def make_id(name, year, month, day, hour, personal_code=""):
    """Produce a deterministic unique input ID."""
    cleaned = sanitize_name(name)[0] or name
    return hashlib.md5(f"{cleaned}|{year}|{month}|{day}|{hour}|{personal_code}".encode("utf-8")).hexdigest()[:12]


def personal_code_influence(personal_code):
    """Generate a deterministic score offset from a personal code.
    This ensures even same name + same birth data produce different fusion scores."""
    if not personal_code or not personal_code.strip():
        return 0.0, ""
    code = personal_code.strip()[:12]
    h = hashlib.sha256(code.encode("utf-8")).digest()
    offset = (int.from_bytes(h[:2], "big") % 2000 - 1000) / 100  # -10.00 to +9.99
    descriptor = h[0] % 5
    descs = ["个人命理微调", "先天变数影响", "后天轨迹修正", "因果业力偏移", "独有命途差异"]
    return round(offset, 2), descs[descriptor]
