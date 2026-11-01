"""LLM enhancer v4 — Cerebras API (OpenAI-compatible, gemma-4-31b)."""
import os, json
from openai import OpenAI
import httpx
from dotenv import load_dotenv

_env_loaded = False
def _ensure_env():
    global _env_loaded
    if not _env_loaded:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        _env_loaded = True

PROXY = "http://127.0.0.1:10808"
MODEL = "gemma-4-31b"
CEREBRAS_KEY = ""
CEREBRAS_BASE = "https://api.cerebras.ai/v1"

_client = None

def _get_client():
    global _client
    _ensure_env()
    if _client is not None:
        return _client
    key = os.environ.get("CEREBRAS_API_KEY", CEREBRAS_KEY)
    if not key:
        return None
    try:
        transport = httpx.HTTPTransport(proxy=PROXY)
        http_client = httpx.Client(transport=transport, timeout=120)
        _client = OpenAI(api_key=key, base_url=CEREBRAS_BASE, http_client=http_client)
        return _client
    except Exception:
        return None

SYSTEM_PROMPT = """你是一位顶尖的八字命理大师，精通子平八字、纳音五行、神煞体系。你的分析必须：
1. 以日主为核心，结合五行生克制化
2. 每个结论都要有干支依据
3. 使用专业命理术语
4. 大运流年分析结合具体干支相互作用
5. 建议要具体可操作"""

def _call(messages, max_tokens=4000, temp=0.7):
    client = _get_client()
    if client is None:
        return None
    model = os.environ.get("LLM_MODEL", MODEL)
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                messages=messages, model=model,
                temperature=temp, max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            if content:
                content = content.strip()
            if "<think>" in content or "<thinking>" in content:
                for tag in ["<think>", "<thinking>"]:
                    if tag in content:
                        content = content.split(tag)[-1]
                        close = tag.replace("<", "</")
                        if close in content:
                            content = content.split(close, 1)[-1]
            return content.strip() if content else None
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower():
                import time
                time.sleep(15 * (attempt + 1))
                continue
            if attempt < 2:
                import time
                time.sleep(5)
                continue
            return None
    return None

def enhance_report(report_data):
    """Single comprehensive call to generate all LLM sections."""
    client = _get_client()
    if client is None:
        return report_data

    bazi = report_data.get("bazi_summary", {})
    fusion = report_data.get("fusion", {})
    timeline = report_data.get("yearly_timeline", [])
    current = report_data.get("metadata", {}).get("current_year", 2026)
    career_data = report_data.get("career", {})

    bazi_str = bazi.get("八字", "")
    dm_el = bazi.get("日主", "")
    wuxing = bazi.get("五行", {})
    wx_str = f"金{wuxing.get('金',0)} 木{wuxing.get('木',0)} 水{wuxing.get('水',0)} 火{wuxing.get('火',0)} 土{wuxing.get('土',0)}"

    # Past years (last 15)
    past_years = [t for t in timeline if t["year"] <= current][-15:]
    past_lines = []
    for ty in past_years:
        ev = "; ".join(e["text"] for e in ty.get("events", [])[:2])
        bad = ",".join(ty.get("spirits_bad", [])) or "-"
        good = ",".join(ty.get("spirits_good", [])) or "-"
        past_lines.append(
            f"[{ty['year']}.{ty['age']}s.{ty['gan_zhi']}] "
            f"C{ty['scores']['career']}W{ty['scores']['wealth']}L{ty['scores']['love']}H{ty['scores']['health']} "
            f"|+{good} |-{bad} |{ev}"
        )
    past_text = "\n".join(past_lines)

    # Future 10 years
    future_years = [t for t in timeline if t["is_future"] and t["year"] <= current + 10]
    future_lines = []
    for ty in future_years:
        ev = "; ".join(e["text"] for e in ty.get("events", [])[:2])
        bad = ",".join(ty.get("spirits_bad", [])) or "-"
        good = ",".join(ty.get("spirits_good", [])) or "-"
        dy = ty.get("da_yun", {}).get("大运", "")
        future_lines.append(
            f"[{ty['year']}.{ty['age']}s.{ty['gan_zhi']} DY:{dy}] "
            f"C{ty['scores']['career']}W{ty['scores']['wealth']}L{ty['scores']['love']}"
            f"H{ty['scores']['health']}F{ty['scores']['family']} "
            f"|+{good} |-{bad} |{ev}"
        )
    future_text = "\n".join(future_lines)

    dy_list = report_data.get("da_yun", [])
    dy_summary = " -> ".join(f"{d.get('大运','')}({d['start_age']}-{d['start_age']+9}s)" for d in dy_list[:6])
    cal = report_data.get("calibration", {})
    cal_str = f"cal:{cal.get('matched_events',0)}/{cal.get('total_events',0)}={cal.get('accuracy',0)}%" if cal.get("calibrated") else "raw"

    # User's real events for calibration
    cal_events = report_data.get("calibration_events_used", [])
    cal_text = ""
    if cal_events:
        cal_lines = [f"  {e['year']}: {e['event']}" for e in cal_events]
        cal_text = "USER CONFIRMED EVENTS:\n" + "\n".join(cal_lines)

    prompt = f"""Analyze this Bazi comprehensively. Output in Chinese.

BASIC INFO:
Bazi={bazi_str}
DayMaster={dm_el}
Wuxing={wx_str}
Personality={bazi.get('性格','')}
Score={fusion.get('score',0)}/100
DaYun={dy_summary}
Career={','.join(career_data.get('overlap',[]))}
{cal_str}

{cal_text}

PAST 15 YEARS:
{past_text}

FUTURE 10 YEARS:
{future_text}

REQUIRED OUTPUT FORMAT (用中文):

【性格剖析】
(Day master analysis, wuxing balance, personality traits - 400+ chars)

【事业财运】
(Career fit, wealth type, key career ages - 400+ chars)

【过去回顾】
(Per year analysis, 80-100 chars each. Align with user's real events if provided.)
FORMAT: YYYY: text

【未来十年推算】
(Per year deep analysis, 250-400 chars each. Include: bazi interaction, career, wealth, love, health, advice.)
FORMAT: YYYY: text

【人生建议】
(Overall advice - 400+ chars)"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    result = _call(messages, max_tokens=6000)
    if not result:
        return report_data

    # Parse sections
    current_sec = None
    current_text = []
    sec_map = {
        "【性格剖析】": "_llm_personality",
        "【事业财运】": "_llm_career",
        "【过去回顾】": "_llm_years",
        "【未来十年推算】": "_llm_future",
        "【人生建议】": "_llm_advice",
    }

    for line in result.split("\n"):
        matched = None
        for h, k in sec_map.items():
            if h in line:
                matched = k
                break
        if matched:
            if current_sec and current_text:
                _store(report_data, current_sec, current_text)
            current_sec = matched
            current_text = []
        else:
            current_text.append(line)
    if current_sec and current_text:
        _store(report_data, current_sec, current_text)

    return report_data

def _store(report_data, key, lines):
    text = "\n".join(lines).strip()
    if not text:
        return
    if key in ("_llm_personality", "_llm_career", "_llm_advice"):
        report_data[key] = text
    elif key in ("_llm_years", "_llm_future"):
        d = {}
        yr_range = range(1990, 2030) if key == "_llm_years" else range(2027, 2040)
        for line in lines:
            stripped = line.strip()
            for yr in yr_range:
                s = str(yr)
                # Match patterns: "年份:", "**年份年**", "年份年", "【年份年】"
                if any(p in stripped for p in [f"{s}:", f"**{s}", f"{s}年:", f"**{s}年**", f"【{s}年】"]):
                    if s not in d:
                        d[s] = []
                    d[s].append(stripped)
                    break
        if d:
            combined = {k: " ".join(v) for k, v in d.items()}
            report_data[key] = combined
        else:
            # Store raw as single entry
            report_data[key] = {"raw": text[:800]}
