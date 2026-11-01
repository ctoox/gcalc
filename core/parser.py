import re
from datetime import datetime

class InputParser:
    def parse_birth_info(self, text):
        patterns = [
            r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?\s*(\d{1,2})?[点时]?",
            r"(\d{4})(\d{2})(\d{2})(\d{2})?"
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                parts = [int(x) if x else 0 for x in m.groups()]
                return {
                    "year": parts[0],
                    "month": parts[1],
                    "day": parts[2],
                    "hour": parts[3] if len(parts) > 3 else 12
                }
        return None

    def parse_question(self, text):
        categories = ["事业", "感情", "健康", "财运", "学业"]
        for cat in categories:
            if cat in text:
                return cat
        return "general"
