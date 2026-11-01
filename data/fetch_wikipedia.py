import requests
import json
import os
import re
import time
from datetime import datetime

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData"
PROXIES = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}
USE_PROXY = True
REQUEST_DELAY = 1.0
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

CELEBRITY_LIST = [
    "Albert Einstein", "Marie Curie", "Isaac Newton", "Nikola Tesla",
    "Charles Darwin", "Galileo Galilei", "Leonardo da Vinci",
    "Wolfgang Amadeus Mozart", "Ludwig van Beethoven", "Johann Sebastian Bach",
    "William Shakespeare", "Fyodor Dostoevsky", "Leo Tolstoy",
    "Socrates", "Plato", "Aristotle", "Confucius",
    "Napoleon Bonaparte", "Abraham Lincoln", "Winston Churchill",
    "Vincent van Gogh", "Pablo Picasso", "Michelangelo",
    "Alan Turing", "Richard Feynman", "Stephen Hawking",
    "Sun Tzu", "Lao Tzu", "Mencius",
    "Florence Nightingale", "Mother Teresa", "Mahatma Gandhi",
    "Sima Qian", "Li Bai", "Du Fu", "Su Shi",
    "Zu Chongzhi", "Zhang Heng", "Shen Kuo",
    "Cao Xueqin", "Lu Xun", "Mo Yan",
]

_LAST_REQUEST = 0.0

def _rate_limit():
    global _LAST_REQUEST
    elapsed = time.time() - _LAST_REQUEST
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)
    _LAST_REQUEST = time.time()

def _get_proxies():
    return PROXIES if USE_PROXY else None

def fetch_wikidata(qid):
    url = f"{WIKIDATA_API}/{qid}.json"
    _rate_limit()
    try:
        resp = requests.get(url, proxies=_get_proxies(), timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[wiki] Wikidata error for {qid}: {e}")
    return None

def parse_wikidata_date(wd_data, prop_id):
    entities = wd_data.get("entities", {})
    for entity in entities.values():
        claims = entity.get("claims", {})
        claim_list = claims.get(prop_id, [])
        for claim in claim_list:
            mainsnak = claim.get("mainsnak", {})
            if mainsnak.get("datatype") == "time":
                datavalue = mainsnak.get("datavalue", {})
                value = datavalue.get("value", {})
                time_str = value.get("time", "")
                m = re.match(r"[+-](\d{4})(?:-(\d{2})(?:-(\d{2}))?)?", time_str)
                if m:
                    return {
                        "year": int(m.group(1)),
                        "month": int(m.group(2)) if m.group(2) else 1,
                        "day": int(m.group(3)) if m.group(3) else 1,
                    }
    return None

def search_wikipedia(title):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": title,
        "format": "json",
        "srlimit": 1,
    }
    _rate_limit()
    try:
        resp = requests.get(WIKI_API, params=params, proxies=_get_proxies(), timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("search", [])
        if pages:
            return pages[0]["title"], pages[0]["pageid"]
    except Exception as e:
        print(f"[wiki] Search error for {title}: {e}")
    return None, None

def fetch_page_props(page_title):
    params = {
        "action": "query",
        "titles": page_title,
        "prop": "pageprops|extracts|info",
        "exintro": True,
        "explaintext": True,
        "inprop": "url",
        "format": "json",
    }
    _rate_limit()
    try:
        resp = requests.get(WIKI_API, params=params, proxies=_get_proxies(), timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if pid != "-1":
                props = page.get("pageprops", {})
                return {
                    "page_id": pid,
                    "title": page.get("title", ""),
                    "extract": page.get("extract", ""),
                    "fullurl": page.get("fullurl", ""),
                    "wikibase_item": props.get("wikibase_item", ""),
                }
    except Exception as e:
        print(f"[wiki] Props error for {page_title}: {e}")
    return None

def extract_birth_death_from_extract(extract):
    birth = death = None
    patterns = [
        (r"(?:born|生[于於]?)\s*:?\s*(\d{4})\s*(?:年)?(?:[/\-\.](\d{1,2}))?(?:[/\-\.](\d{1,2}))?", "birth"),
        (r"(?:died|卒[于於]?|殁[于於]?)\s*:?\s*(\d{4})\s*(?:年)?(?:[/\-\.](\d{1,2}))?(?:[/\-\.](\d{1,2}))?", "death"),
        (r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?\s*[-–—]\s*(\d{4})", "lifespan"),
    ]
    for pat, ptype in patterns:
        m = re.search(pat, extract)
        if m:
            if ptype == "birth":
                birth = {"year": int(m.group(1)), "month": int(m.group(2) or 1), "day": int(m.group(3) or 1)}
            elif ptype == "death":
                death = {"year": int(m.group(1)), "month": int(m.group(2) or 1), "day": int(m.group(3) or 1)}
            elif ptype == "lifespan":
                birth = {"year": int(m.group(1)), "month": 1, "day": 1}
                death = {"year": int(m.group(4)), "month": 1, "day": 1}
    return birth, death

def fetch_celebrity(name):
    page_title, page_id = search_wikipedia(name)
    if not page_title:
        print(f"[wiki] Not found: {name}")
        return None

    props = fetch_page_props(page_title)
    if not props:
        return None

    wikibase_item = props.get("wikibase_item", "")
    birth = death = None

    if wikibase_item:
        wd_data = fetch_wikidata(wikibase_item)
        if wd_data:
            birth = parse_wikidata_date(wd_data, "P569")
            death = parse_wikidata_date(wd_data, "P570")

    if not birth or not death:
        extract_birth, extract_death = extract_birth_death_from_extract(props.get("extract", ""))
        if not birth:
            birth = extract_birth
        if not death:
            death = extract_death

    result = {
        "name": page_title,
        "birth_year": birth["year"] if birth else 0,
        "birth_month": birth["month"] if birth else 1,
        "birth_day": birth["day"] if birth else 1,
        "death_year": death["year"] if death else None,
        "death_month": death["month"] if death else None,
        "death_day": death["day"] if death else None,
        "wiki_url": props.get("fullurl", ""),
        "wikidata_id": wikibase_item,
        "source": "wikipedia",
        "fetched_at": str(datetime.now()),
    }
    print(f"[wiki] Fetched: {page_title} ({result['birth_year']}-{result.get('death_year', '')})")
    return result

def fetch_batch(names=None, output=None):
    if names is None:
        names = CELEBRITY_LIST
    if output is None:
        output = os.path.join(DATA_DIR, "wikipedia_celebrities.json")

    results = []
    for i, name in enumerate(names):
        print(f"[wiki] [{i+1}/{len(names)}] Fetching: {name}")
        try:
            result = fetch_celebrity(name)
            if result:
                results.append(result)
        except Exception as e:
            print(f"[wiki] Error fetching {name}: {e}")

    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[wiki] Batch complete: {len(results)}/{len(names)} fetched -> {output}")
    return results

if __name__ == "__main__":
    fetch_batch()
