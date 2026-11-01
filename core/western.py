from datetime import date

class WesternEngine:
    SUN_SIGNS = [
        (120, "摩羯"), (218, "水瓶"), (320, "双鱼"), (420, "白羊"),
        (521, "金牛"), (621, "双子"), (722, "巨蟹"), (823, "狮子"),
        (923, "处女"), (1023, "天秤"), (1122, "天蝎"), (1222, "射手"),
        (1231, "摩羯"),
    ]
    SIGN_EN = {
        "白羊":"Aries","金牛":"Taurus","双子":"Gemini","巨蟹":"Cancer",
        "狮子":"Leo","处女":"Virgo","天秤":"Libra","天蝎":"Scorpio",
        "射手":"Sagittarius","摩羯":"Capricorn","水瓶":"Aquarius","双鱼":"Pisces",
    }
    ELEMENTS = {
        "白羊":"火","狮子":"火","射手":"火",
        "金牛":"土","处女":"土","摩羯":"土",
        "双子":"风","天秤":"风","水瓶":"风",
        "巨蟹":"水","天蝎":"水","双鱼":"水",
    }
    MODALITIES = {
        "白羊":"本位","巨蟹":"本位","天秤":"本位","摩羯":"本位",
        "金牛":"固定","狮子":"固定","天蝎":"固定","水瓶":"固定",
        "双子":"变动","处女":"变动","射手":"变动","双鱼":"变动",
    }
    PLANET_RULERS = {
        "白羊":"火星","金牛":"金星","双子":"水星","巨蟹":"月亮",
        "狮子":"太阳","处女":"水星","天秤":"金星","天蝎":"冥王星",
        "射手":"木星","摩羯":"土星","水瓶":"天王星","双鱼":"海王星",
    }
    HOUSES = [
        "命宫", "财帛宫", "兄弟宫", "田宅宫", "子女宫", "奴仆宫",
        "夫妻宫", "疾厄宫", "迁移宫", "官禄宫", "福德宫", "玄秘宫",
    ]

    def _day_of_year(self, m, d):
        days_in_month = [0,31,28,31,30,31,30,31,31,30,31,30,31]
        return sum(days_in_month[:m]) + d

    def get_sun_sign(self, month, day):
        doy = self._day_of_year(month, day)
        for cutoff, sign in self.SUN_SIGNS:
            if doy <= cutoff:
                return sign
        return "摩羯"

    def calculate_chart(self, birth_date, birth_time, lat=None, lng=None):
        month = birth_date.month
        day = birth_date.day
        sun_sign = self.get_sun_sign(month, day)
        element = self.ELEMENTS.get(sun_sign, "?")
        modality = self.MODALITIES.get(sun_sign, "?")
        ruler = self.PLANET_RULERS.get(sun_sign, "?")

        moon_raw = ((month * 2 + day // 7) % 12)
        moon_sign = self.SUN_SIGNS[moon_raw][1] if moon_raw < 12 else "摩羯"
        moon_element = self.ELEMENTS.get(moon_sign, "?")

        rising_raw = (month + (birth_time // 2) + (lng or 0)) % 12
        rising_sign = self.SUN_SIGNS[rising_raw][1] if 0 <= rising_raw < 12 else "摩羯"
        rising_element = self.ELEMENTS.get(rising_sign, "?")

        planet_positions = {}
        for i, p in enumerate(["太阳","月亮","水星","金星","火星","木星","土星","天王星","海王星","冥王星"]):
            p_raw = (month + i * 2) % 12
            p_sign = self.SUN_SIGNS[p_raw][1] if p_raw < 12 else "摩羯"
            planet_positions[p] = {"sign": p_sign, "element": self.ELEMENTS.get(p_sign, "?")}

        houses = []
        for i, h in enumerate(self.HOUSES):
            h_raw = (rising_raw + i) % 12
            h_sign = self.SUN_SIGNS[h_raw][1] if h_raw < 12 else "摩羯"
            houses.append({"house": h, "sign": h_sign})

        element_balance = {}
        for e in ["火","土","风","水"]:
            element_balance[e] = 0
        element_balance[element] = element_balance.get(element, 0) + 3
        element_balance[moon_element] = element_balance.get(moon_element, 0) + 2
        element_balance[rising_element] = element_balance.get(rising_element, 0) + 2
        for p, info in planet_positions.items():
            pe = info["element"]
            element_balance[pe] = element_balance.get(pe, 0) + 1
        total = sum(element_balance.values()) or 1

        return {
            "sun_sign": sun_sign,
            "sun_sign_en": self.SIGN_EN.get(sun_sign, ""),
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "element": element,
            "modality": modality,
            "ruler_planet": ruler,
            "element_balance": {k: f"{v/total*100:.0f}%" for k,v in sorted(element_balance.items(), key=lambda x:-x[1])},
            "dominant_element": max(element_balance, key=element_balance.get),
            "houses": houses,
            "planet_positions": planet_positions,
            "personality": self._personality_traits(sun_sign, element, modality),
            "career_hints": self._career_hints(sun_sign, element),
        }

    def _personality_traits(self, sun_sign, element, modality):
        traits = {
            "白羊": "勇敢直率, 喜欢挑战, 领导力强, 但易冲动",
            "金牛": "稳重务实, 有耐心, 审美力强, 但易固执",
            "双子": "聪明灵活, 善于沟通, 好奇心强, 但易浮躁",
            "巨蟹": "敏感体贴, 家庭观念强, 直觉准, 但易情绪化",
            "狮子": "自信大方, 有领导魅力, 创造力强, 但易自负",
            "处女": "细致严谨, 追求完美, 分析力强, 但易挑剔",
            "天秤": "优雅公正, 善于社交, 审美力强, 但易犹豫",
            "天蝎": "深刻执着, 洞察力强, 意志坚定, 但易极端",
            "射手": "乐观自由, 热爱探索, 哲学思维, 但易冲动",
            "摩羯": "踏实坚韧, 目标明确, 管理力强, 但易保守",
            "水瓶": "创新独立, 思想超前, 人道主义, 但易叛逆",
            "双鱼": "富有想象力, 同情心强, 艺术天赋, 但易逃避",
        }
        base = traits.get(sun_sign, "综合型")
        return f"{modality}{element}座: {base}"

    def _career_hints(self, sun_sign, element):
        careers = {
            "白羊": ["管理", "创业", "体育", "军事", "销售"],
            "金牛": ["金融", "艺术", "餐饮", "房地产", "设计"],
            "双子": ["传媒", "教育", "编程", "写作", "翻译"],
            "巨蟹": ["教育", "心理学", "护理", "房地产", "餐饮"],
            "狮子": ["管理", "演艺", "政界", "创业", "设计"],
            "处女": ["医疗", "分析", "编程", "会计", "研究"],
            "天秤": ["法律", "外交", "艺术", "公关", "设计"],
            "天蝎": ["研究", "侦查", "心理咨询", "投资", "医疗"],
            "射手": ["教育", "出版", "旅行", "法律", "哲学"],
            "摩羯": ["管理", "金融", "建筑", "公务员", "工程"],
            "水瓶": ["科技", "研发", "社会公益", "艺术", "航天"],
            "双鱼": ["艺术", "医疗", "慈善", "电影", "写作"],
        }
        return careers.get(sun_sign, ["综合"])

    def numerology(self, birth_date):
        total = sum(int(d) for d in birth_date.strftime("%Y%m%d"))
        life_path = total
        while life_path > 9:
            life_path = sum(int(d) for d in str(life_path))
        digits = [int(d) for d in birth_date.strftime("%Y%m%d")]
        expression = sum(digits)
        while expression > 9:
            expression = sum(int(d) for d in str(expression))
        return {
            "life_path": life_path,
            "life_path_meaning": self._life_path_meaning(life_path),
            "expression": expression,
        }

    def _life_path_meaning(self, n):
        meanings = {
            1: "领导者, 独立创新, 适合开创性事业",
            2: "协调者, 善于合作, 适合外交调解",
            3: "表达者, 创造力强, 适合艺术传媒",
            4: "建设者, 踏实可靠, 适合工程管理",
            5: "探索者, 热爱自由, 适合旅行销售",
            6: "守护者, 责任感强, 适合教育医疗",
            7: "思想家, 深度分析, 适合研究哲学",
            8: "成就者, 商业头脑, 适合企业管理",
            9: "人道主义者, 大爱无私, 适合公益慈善",
        }
        return meanings.get(n, "综合发展")
