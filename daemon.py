"""
gcalc Data Collection Daemon
Runs in background, slowly but continuously collects global human records.
Sources: Wikipedia (multi-lang), Wikidata, DBpedia, Open Library, local archives.
Port range: 20003 (status API), 20004 (admin)
"""

import sys, os, json, time, threading, logging, signal, socket
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from collector import DataCollector, Person, LifeEvent

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

LOG = logging.getLogger("gcalc-daemon")
LOG.setLevel(logging.INFO)
fh = logging.FileHandler(os.path.join(DATA_DIR, "daemon.log"), encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
LOG.addHandler(fh)
LOG.addHandler(logging.StreamHandler())

STATUS_FILE = os.path.join(DATA_DIR, "daemon_status.json")
MASTER_FILE = os.path.join(DATA_DIR, "persons_master.json")

class CollectorDaemon:
    def __init__(self):
        self.running = False
        self.paused = False
        self.stats = {"total_fetched": 0, "sources": {}, "last_run": None, "errors": 0}
        self._load_status()
        self.sources = [
            WikiSource(self),
            WikidataSource(self),
            LocalArchiveSource(self),
        ]
        self.httpd = None

    def _load_status(self):
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r") as f:
                    self.stats = json.load(f)
            except Exception:
                pass

    def _save_status(self):
        self.stats["last_run"] = str(datetime.now())
        with open(STATUS_FILE, "w") as f:
            json.dump(self.stats, f, indent=2)

    def start(self):
        self.running = True
        LOG.info("=== gcalc Daemon STARTED ===")
        status_thread = threading.Thread(target=self._status_server, daemon=True)
        status_thread.start()
        while self.running:
            if not self.paused:
                for source in self.sources:
                    if not self.running:
                        break
                    try:
                        count = source.collect()
                        if count:
                            src_name = source.__class__.__name__
                            self.stats["sources"][src_name] = self.stats["sources"].get(src_name, 0) + count
                            self.stats["total_fetched"] += count
                            self._save_status()
                            LOG.info(f"[{src_name}] +{count} persons (total: {self.stats['total_fetched']})")
                    except Exception as e:
                        self.stats["errors"] += 1
                        LOG.error(f"Source error {source.__class__.__name__}: {e}")
                self._save_status()
                self._merge_all()
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1)

    def stop(self):
        LOG.info("Daemon stopping...")
        self.running = False

    def _status_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", 20003))
            sock.listen(5)
            sock.settimeout(2)
            LOG.info("Status API on 127.0.0.1:20003")
            while self.running:
                try:
                    conn, addr = sock.accept()
                    data = conn.recv(1024).decode()
                    if "GET /status" in data:
                        resp = json.dumps(self.stats, indent=2)
                        conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{resp}".encode())
                    elif "GET /pause" in data:
                        self.paused = True
                        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nPAUSED")
                    elif "GET /resume" in data:
                        self.paused = False
                        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nRESUMED")
                    elif "GET /stop" in data:
                        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nSTOPPING")
                        self.stop()
                    else:
                        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\ngcalc daemon running")
                    conn.close()
                except socket.timeout:
                    pass
        except OSError as e:
            LOG.warning(f"Status server port 20003: {e}")
        finally:
            sock.close()

    def _merge_all(self):
        c = DataCollector()
        for fname in os.listdir(DATA_DIR):
            if fname.endswith(".json") and fname not in ("daemon_status.json",):
                fpath = os.path.join(DATA_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for pd in data.get("persons", []):
                        try:
                            p = Person(**{k: v for k, v in pd.items()
                                        if k in Person.__dataclass_fields__ and v is not None})
                            c.add_person(p)
                        except Exception:
                            pass
                    for ed in data.get("events", []):
                        try:
                            e = LifeEvent(**{k: v for k, v in ed.items()
                                           if k in LifeEvent.__dataclass_fields__ and v is not None})
                            c.add_event(e)
                        except Exception:
                            pass
                except Exception:
                    pass
        c.export_json(MASTER_FILE)

class WikiSource:
    def __init__(self, daemon):
        self.daemon = daemon
        self.LANGS = ["en", "zh", "fr", "de", "es", "ja", "ru", "ar", "pt", "it"]
        self.CATEGORIES = [
            "Scientists", "Philosophers", "Writers", "Artists", "Politicians",
            "Musicians", "Inventors", "Explorers", "Mathematicians", "Physicians",
            "Astronomers", "Chemists", "Physicists", "Biologists", "Economists",
            "Nobel_laureates", "Olympic_athletes", "Film_directors", "Architects",
        ]
        self.idx = 0
        self.cat_idx = 0
        self.lang_idx = 0

    def collect(self):
        import requests
        total = 0
        lang = self.LANGS[self.lang_idx % len(self.LANGS)]
        cat = self.CATEGORIES[self.cat_idx % len(self.CATEGORIES)]
        api = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{cat}",
            "cmlimit": "50",
            "cmoffset": self.idx,
            "format": "json",
        }
        try:
            resp = requests.get(api, params=params, timeout=30,
                               headers={"User-Agent": "GCalc/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                members = data.get("query", {}).get("categorymembers", [])
                for m in members:
                    if m.get("ns") == 0:
                        info = self._fetch_person_info(lang, m["title"])
                        if info:
                            self.daemon._save_status()
                            total += 1
                self.idx += 50
                if len(members) < 50:
                    self.idx = 0
                    self.cat_idx += 1
                    if self.cat_idx >= len(self.CATEGORIES):
                        self.cat_idx = 0
                        self.lang_idx += 1
            return total
        except Exception as e:
            LOG.debug(f"WikiSource ({lang}/{cat}): {e}")
            self.cat_idx += 1
            return 0

    def _fetch_person_info(self, lang, title):
        import requests
        api = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "pageprops|extracts",
            "titles": title,
            "exintro": True,
            "explaintext": True,
            "format": "json",
        }
        try:
            resp = requests.get(api, params=params, timeout=15,
                               headers={"User-Agent": "GCalc/1.0"})
            if resp.status_code != 200:
                return None
            data = resp.json()
            for pid, page in data.get("query", {}).get("pages", {}).items():
                if pid == "-1":
                    return None
                extract = page.get("extract", "")
                import re
                by = re.search(r"(?:born|生於|生まれ|né|né)\s*:?\s*(\d{4})", extract)
                dy = re.search(r"(?:died|卒於|死去|mort)\s*:?\s*(\d{4})", extract)
                if not by:
                    by = re.search(r"(\d{4})[年\-\-](\d{1,2})[月\-]", extract)
                by_g = by.groups() if by else None
                out_path = os.path.join(DATA_DIR, "wiki_raw.jsonl")
                record = {
                    "name": page.get("title", title),
                    "lang": lang,
                    "extract": extract[:500],
                    "fetched_at": str(datetime.now()),
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                return record
        except Exception:
            return None

class WikidataSource:
    def __init__(self, daemon):
        self.daemon = daemon
        self.offset = 0
        self.LIMIT = 100
        self.OCCUPATIONS = [
            "Q5", "Q36180", "Q36180", "Q483501", "Q82955",
            "Q33999", "Q20661331", "Q2306090", "Q105543609",
        ]

    def collect(self):
        import requests
        occ = self.OCCUPATIONS[self.offset // 5000 % len(self.OCCUPATIONS)]
        query = f"""
        SELECT ?person ?personLabel ?birthDate ?deathDate ?occLabel ?countryLabel WHERE {{
          ?person wdt:P31 wd:Q5 .
          ?person wdt:P569 ?birthDate .
          OPTIONAL {{ ?person wdt:P570 ?deathDate . }}
          OPTIONAL {{ ?person wdt:P106/wdt:P31 wd:{occ} . }}
          OPTIONAL {{ ?person wdt:P27 ?country . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,en". }}
        }}
        ORDER BY ?person
        LIMIT {self.LIMIT}
        OFFSET {self.offset}
        """
        url = "https://query.wikidata.org/sparql"
        try:
            resp = requests.get(url, params={"format": "json", "query": query},
                               headers={"User-Agent": "GCalc/1.0"}, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", {}).get("bindings", [])
                if not results:
                    self.offset = 0
                    return 0
                out_path = os.path.join(DATA_DIR, "wikidata_raw.jsonl")
                with open(out_path, "a", encoding="utf-8") as f:
                    for row in results:
                        record = {
                            "qid": row.get("person", {}).get("value", "").split("/")[-1],
                            "name": row.get("personLabel", {}).get("value", ""),
                            "birth": row.get("birthDate", {}).get("value", ""),
                            "death": row.get("deathDate", {}).get("value", "") if row.get("deathDate") else None,
                            "occupation": row.get("occLabel", {}).get("value", ""),
                            "country": row.get("countryLabel", {}).get("value", ""),
                            "fetched_at": str(datetime.now()),
                        }
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                self.offset += self.LIMIT
                return len(results)
        except Exception as e:
            LOG.debug(f"WikidataSource: {e}")
            self.offset += self.LIMIT
            return 0

class LocalArchiveSource:
    def __init__(self, daemon):
        self.daemon = daemon
        self.files_scanned = set()

    def collect(self):
        raw_dir = os.path.join(DATA_DIR, "raw")
        if not os.path.isdir(raw_dir):
            os.makedirs(raw_dir, exist_ok=True)
            return 0
        total = 0
        for fname in os.listdir(raw_dir):
            if fname.endswith(".json") and fname not in self.files_scanned:
                fpath = os.path.join(raw_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    archive_file = os.path.join(DATA_DIR, "archive.json")
                    with open(archive_file, "a", encoding="utf-8") as af:
                        af.write(json.dumps({"file": fname, "records": data, "loaded_at": str(datetime.now())}, ensure_ascii=False) + "\n")
                    total += 1
                except Exception as e:
                    LOG.debug(f"LocalArchive: {fname} -> {e}")
                self.files_scanned.add(fname)
        return total

def run_daemon():
    d = CollectorDaemon()
    try:
        d.start()
    except KeyboardInterrupt:
        d.stop()
        LOG.info("Daemon stopped by user")

def status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {"status": "not running"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="gcalc Data Collection Daemon")
    parser.add_argument("--daemon", action="store_true", help="Run as background daemon")
    parser.add_argument("--status", action="store_true", help="Show daemon status")
    parser.add_argument("--stop", action="store_true", help="Stop daemon")
    args = parser.parse_args()

    if args.status:
        s = status()
        print(json.dumps(s, indent=2))
    elif args.stop:
        import socket
        s = socket.socket()
        try:
            s.connect(("127.0.0.1", 20003))
            s.send(b"GET /stop HTTP/1.0\r\n\r\n")
            print("Stop signal sent")
        except ConnectionRefusedError:
            print("Daemon not running")
        finally:
            s.close()
    else:
        run_daemon()
