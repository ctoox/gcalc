class BaziEngine:
    def __init__(self):
        self.tian_gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        self.di_zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        self.wuxing_gan = {"甲":"木", "乙":"木", "丙":"火", "丁":"火", "戊":"土", "己":"土", "庚":"金", "辛":"金", "壬":"水", "癸":"水"}
        self.wuxing_zhi = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
        self.zang_gan = {"子":["癸"],"丑":["己","癸","辛"],"寅":["甲","丙","戊"],"卯":["乙"],"辰":["戊","乙","癸"],"巳":["丙","庚","戊"],"午":["丁","己"],"未":["己","丁","乙"],"申":["庚","壬","戊"],"酉":["辛"],"戌":["戊","辛","丁"],"亥":["壬","甲"]}
        self.wu_hu_dun = {
            0: 2, 1: 4, 2: 6, 3: 8, 4: 0,
            5: 2, 6: 4, 7: 6, 8: 8, 9: 0,
        }
        self.wu_shou_dun = {
            0: 0, 1: 2, 2: 4, 3: 6, 4: 8,
            5: 0, 6: 2, 7: 4, 8: 6, 9: 8,
        }
        self.month_zhi_table = [2, 4, 6, 8, 10, 0]
        # Import lunar_python for accurate 节气-based calculations
        from lunar_python import Solar
        self._Solar = Solar

    def shichen(self, hour):
        if hour is None:
            return "", -1
        idx = ((hour + 1) // 2) % 12
        return self.di_zhi[idx], idx

    def calculate(self, birth_year, birth_month, birth_day, birth_hour=12):
        # ── Accurate pillars via lunar_python (节气-based) ──
        lp_ok = False
        try:
            solar = self._Solar.fromYmd(birth_year, birth_month, birth_day)
            lunar = solar.getLunar()
            nian = lunar.getYearInGanZhiExact()
            yue = lunar.getMonthInGanZhiExact()
            ri = lunar.getDayInGanZhiExact()
            shi = lunar.getTimeInGanZhi()
            lp_ok = True
        except Exception:
            pass

        if not lp_ok:
            # Fallback simplified calculation
            yg = (birth_year - 4) % 10
            yz = (birth_year - 4) % 12
            nian = f"{self.tian_gan[yg]}{self.di_zhi[yz]}"
            yz_mod3 = yz % 3
            mz = (yz_mod3 * 4 + birth_month + 1) % 12
            mg = (self.wu_hu_dun[yg] + birth_month + 1) % 10
            yue = f"{self.tian_gan[mg]}{self.di_zhi[mz]}"
            day_offset = (birth_year - 1) * 365 + (birth_year - 1) // 4 - (birth_year - 1) // 100 + (birth_year - 1) // 400
            month_days = [0,31,28,31,30,31,30,31,31,30,31,30,31]
            if (birth_year % 4 == 0 and birth_year % 100 != 0) or (birth_year % 400 == 0):
                month_days[2] = 29
            for m in range(1, birth_month):
                day_offset += month_days[m]
            day_offset += birth_day
            dg = day_offset % 10
            dz = day_offset % 12
            ri = f"{self.tian_gan[dg]}{self.di_zhi[dz]}"
            hour_zhi_f, hz = self.shichen(birth_hour)
            if hz >= 0:
                hg_start = self.wu_shou_dun.get(dg % 10, 0)
                hg = (hg_start + hz * 2) % 10
                shi = f"{self.tian_gan[hg]}{hour_zhi_f}"
            else:
                shi = ""

        # Parse indices
        yg = self.tian_gan.index(nian[0]) % 10
        yz = self.di_zhi.index(nian[1]) % 12 if len(nian) > 1 else 0
        mg = self.tian_gan.index(yue[0]) % 10
        mz = self.di_zhi.index(yue[1]) % 12 if len(yue) > 1 else 0
        dg = self.tian_gan.index(ri[0]) % 10
        dz = self.di_zhi.index(ri[1]) % 12 if len(ri) > 1 else 0
        hg = self.tian_gan.index(shi[0]) % 10 if shi and len(shi) > 0 else -1
        hour_zhi = shi[1] if shi and len(shi) > 1 else ""
        hz = self.di_zhi.index(hour_zhi) if hour_zhi else -1

        bazi_str = f"{nian} {yue} {ri} {shi}".strip() if shi else f"{nian} {yue} {ri}"
        day_master = ri[0]
        day_master_element = self.wuxing_gan.get(day_master, "土")

        year_element = self.wuxing_gan.get(nian[0], "")
        month_element = self.wuxing_gan.get(yue[0], "")
        day_element = self.wuxing_gan.get(ri[0], "")
        hour_element = self.wuxing_gan.get(shi[0], "") if shi else ""
        elements_in_bazi = [year_element, month_element, day_element, hour_element]

        element_counts = {}
        for e in elements_in_bazi:
            if e:
                element_counts[e] = element_counts.get(e, 0) + 1

        element_strength = max(element_counts.values()) if element_counts else 0
        dominant_element = max(element_counts, key=element_counts.get) if element_counts else "土"
        weak_element = min(element_counts, key=element_counts.get) if element_counts else "土"

        hidden_stems = []
        for zhi_str in [nian[1] if len(nian) > 1 else "",
                        yue[1] if len(yue) > 1 else "",
                        ri[1] if len(ri) > 1 else "",
                        shi[1] if shi and len(shi) > 1 else ""]:
            if zhi_str:
                hidden = self.zang_gan.get(zhi_str, [])
                for h in hidden:
                    ze = self.wuxing_gan.get(h, "")
                    if ze:
                        hidden_stems.append(ze)

        for hs in hidden_stems:
            element_counts[hs] = element_counts.get(hs, 0) + 0.5

        na_yin = {
            ("甲","子"):"海中金", ("乙","丑"):"海中金", ("丙","寅"):"炉中火", ("丁","卯"):"炉中火",
            ("戊","辰"):"大林木", ("己","巳"):"大林木", ("庚","午"):"路旁土", ("辛","未"):"路旁土",
            ("壬","申"):"剑锋金", ("癸","酉"):"剑锋金", ("甲","戌"):"山头火", ("乙","亥"):"山头火",
            ("丙","子"):"涧下水", ("丁","丑"):"涧下水", ("戊","寅"):"城头土", ("己","卯"):"城头土",
            ("庚","辰"):"白蜡金", ("辛","巳"):"白蜡金", ("壬","午"):"杨柳木", ("癸","未"):"杨柳木",
            ("甲","申"):"泉中水", ("乙","酉"):"泉中水", ("丙","戌"):"屋上土", ("丁","亥"):"屋上土",
            ("戊","子"):"霹雳火", ("己","丑"):"霹雳火", ("庚","寅"):"松柏木", ("辛","卯"):"松柏木",
            ("壬","辰"):"长流水", ("癸","巳"):"长流水", ("甲","午"):"沙中金", ("乙","未"):"沙中金",
            ("丙","申"):"山下火", ("丁","酉"):"山下火", ("戊","戌"):"平地木", ("己","亥"):"平地木",
            ("庚","子"):"壁上土", ("辛","丑"):"壁上土", ("壬","寅"):"金箔金", ("癸","卯"):"金箔金",
            ("甲","辰"):"覆灯火", ("乙","巳"):"覆灯火", ("丙","午"):"天河水", ("丁","未"):"天河水",
            ("戊","申"):"大驿土", ("己","酉"):"大驿土", ("庚","戌"):"钗钏金", ("辛","亥"):"钗钏金",
            ("壬","子"):"桑柘木", ("癸","丑"):"桑柘木",
        }
        nayin = na_yin.get((nian[0], nian[1]), "") if len(nian) > 1 else ""

        self_generating = self._generating_cycle(day_master_element)
        self_controlling = self._controlling_cycle(day_master_element)

        missing_elements = [e for e in ["木","火","土","金","水"] if e not in element_counts or element_counts[e] == 0]

        return {
            "bazi": bazi_str,
            "four_pillars": {
                "year": {"gan": nian[0], "zhi": nian[1] if len(nian) > 1 else "", "na_yin": nayin},
                "month": {"gan": yue[0], "zhi": yue[1] if len(yue) > 1 else ""},
                "day": {"gan": ri[0], "zhi": ri[1] if len(ri) > 1 else ""},
                "hour": {"gan": shi[0] if shi else "", "zhi": hour_zhi},
            },
            "day_master": day_master,
            "day_master_element": day_master_element,
            "elements": {
                "day_master": day_master_element,
                "counts": dict(sorted(element_counts.items(), key=lambda x: -x[1])),
                "dominant": dominant_element,
                "weak": weak_element,
                "missing": missing_elements,
                "generates": self_generating,
                "controls": self_controlling,
            },
            "hidden_stems": hidden_stems,
            "personality": self._analyze_personality(day_master_element, dominant_element, missing_elements),
            "career_affinity": self._career_affinity(day_master_element, dominant_element),
            "wealth_potential": self._wealth_potential(element_counts, day_master_element),
        }

    def _generating_cycle(self, element):
        cycle = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        return cycle.get(element, "")

    def _controlling_cycle(self, element):
        cycle = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
        return cycle.get(element, "")

    def _analyze_personality(self, day_master, dominant, missing):
        profiles = {
            "木": "仁厚, 有同情心, 善于规划, 但易固执",
            "火": "热情开朗, 有领导力, 行动力强, 但易急躁",
            "土": "稳重踏实, 守信可靠, 善于管理, 但易保守",
            "金": "果断刚毅, 有魄力, 善于决策, 但易刚愎",
            "水": "智慧灵活, 善于变通, 有洞察力, 但易多变",
        }
        base = profiles.get(day_master, "中庸")
        if missing:
            base += f" | 缺{'/'.join(missing)}, 需补相应五行"
        return base

    def _career_affinity(self, day_master, dominant):
        careers = {
            "木": ["教育", "文化", "艺术", "出版", "医疗", "环保", "设计"],
            "火": ["管理", "科技", "互联网", "能源", "军事", "体育", "创业"],
            "土": ["房地产", "建筑", "农业", "金融", "人力资源", "公务员"],
            "金": ["法律", "金融", "投资", "医疗外科", "机械", "军警", "咨询"],
            "水": ["贸易", "物流", "传媒", "旅游", "外交", "心理咨询", "艺术"],
        }
        return careers.get(day_master, ["综合"])

    def _wealth_potential(self, element_counts, day_master):
        wealth_element = self._controlling_cycle(day_master)
        wealth_score = element_counts.get(wealth_element, 0) * 20
        if wealth_element in element_counts:
            wealth_score += 30
        level = "高" if wealth_score >= 60 else "中" if wealth_score >= 30 else "低"
        return {"score": min(100, wealth_score), "level": level, "wealth_element": wealth_element}

    def fortune_cycles(self, birth_year, gender="男"):
        """Calculate 大运 (10-year fortune cycles)"""
        yg = (birth_year - 4) % 10
        yz = (birth_year - 4) % 12
        yang_years = [0, 2, 4, 6, 8]
        is_yang = yg in yang_years
        forward = (is_yang and gender == "男") or (not is_yang and gender != "男")

        start_age = ((yz * 3) % 12) + 1
        cycles = []
        for i in range(8):
            age = start_age + i * 10
            offset = i if forward else -i
            cyc_gan = (yg + offset) % 10
            cyc_zhi = (yz + offset) % 12
            cycles.append({
                "age_range": f"{age}-{age+9}",
                "pillar": f"{self.tian_gan[cyc_gan]}{self.di_zhi[cyc_zhi]}",
                "element": self.wuxing_gan.get(self.tian_gan[cyc_gan], ""),
            })
        return {"start_age": start_age, "cycles": cycles, "forward": forward}

    def annual_fortune(self, birth_year, birth_month, birth_day, target_year):
        """Calculate 流年 fortune for a specific year"""
        yg = (target_year - 4) % 10
        yz = (target_year - 4) % 12
        nian_gan = self.tian_gan[yg]
        nian_zhi = self.di_zhi[yz]
        element = self.wuxing_gan.get(nian_gan, "")
        zodiac_idx = yz
        zodiac_names = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake","Horse","Goat","Monkey","Rooster","Dog","Pig"]
        zodiac = zodiac_names[zodiac_idx]

        bazi = self.calculate(birth_year, birth_month, birth_day)
        dm = bazi["day_master_element"]
        conflict = self._controlling_cycle(element) == dm or self._generating_cycle(element) == dm

        age = target_year - birth_year
        if age < 60:
            ben_ming = (yz == (birth_year - 4) % 12)
        else:
            ben_ming = False

        return {
            "year": target_year,
            "nian_gan": nian_gan,
            "nian_zhi": nian_zhi,
            "element": element,
            "zodiac": zodiac,
            "age": age,
            "ben_ming_nian": ben_ming,
            "conflict_with_day_master": conflict,
            "favorable": "吉" if not conflict else "凶",
        }
