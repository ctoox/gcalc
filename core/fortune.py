import random
from datetime import date

class FortuneEngine:
    def daily_fortune(self, bazi, target_date=None):
        if target_date is None:
            target_date = date.today()
        return {
            "date": str(target_date),
            "overall": random.choice(["吉", "中吉", "小吉", "平", "小凶", "凶"]),
            "aspects": {
                "career": random.choice(["顺利", "波动", "平稳"]),
                "love": random.choice(["桃花旺盛", "平淡", "注意沟通"]),
                "health": random.choice(["良好", "注意休息", "小恙"])
            },
            "lucky_color": random.choice(["红", "黄", "蓝", "绿", "紫"]),
            "lucky_number": random.randint(1, 9)
        }

    def yearly_fortune(self, bazi, year):
        return {
            "year": year,
            "overall_rank": random.choice(["上上", "中上", "中", "中下", "下"]),
            "key_factors": ["流年", "大运", "神煞"]
        }
