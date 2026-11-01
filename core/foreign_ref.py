"""Foreign (Western/Eastern) divination systems reference.
Lists systems that share common roots with Chinese 命理,
and can be integrated for cross-validation."""

FOREIGN_SYSTEMS = {
    "Vedic Astrology (Jyotish)": {
        "origin": "India, ~5000 years",
        "commonality": "Uses 9 planets (Navagraha), 27 lunar mansions (Nakshatra), "
                       "12 houses (Bhavas). Concept of Karma (= 因果) and "
                       "reincarnation. Dashas (planetary periods) = 大运.",
        "key_elements": "5 elements (Pancha Mahabhuta): 地/Earth, 水/Water, "
                        "火/Fire, 风/Air, 空/Ether. Maps to Chinese 五行: "
                        "土=Earth, 水=Water, 火=Fire, 金=Metal=Air, 木=Wood.",
        "integration": "Nakshatra (27 lunar houses) × 4 padas = 108 divisions, "
                       "similar to 28 宿 in Chinese astrology. Can cross-reference "
                       "sun sign + nakshatra for personality.",
        "accident_death": "Sudden death indicators: 8th house (longevity), "
                          "Saturn + Mars conjunction (violence), "
                          "Kemadruma yoga (no planets around Moon).",
    },
    "Western Astrology (Tropical)": {
        "origin": "Babylon/Greece, ~4000 years",
        "commonality": "12 signs, 12 houses, planets. "
                       "Progressed chart = 大运. Solar return = 流年.",
        "key_elements": "Fire/Earth/Air/Water = 火/土/风/水. "
                        "Chinese adds 木 (Wood) as 5th element.",
        "integration": "Already integrated in core/western.py. "
                       "Can add: progressed Moon (monthly emotions = 流月), "
                       "solar arc (yearly direction = 流年).",
        "accident_death": "Mars/Pluto/Uranus hard aspects to Sun/Moon = sudden events. "
                          "8th house Pluto = transformative death. "
                          "Saturn in 8th = long illness.",
    },
    "Zi Wei Dou Shu (紫微斗数)": {
        "origin": "China, Song Dynasty ~1000 AD",
        "commonality": "Chinese system parallel to BaZi. Uses 12 palaces (命盘) "
                       "like Western houses. 14 main stars.",
        "key_elements": "紫微星 (Emperor star), 天府星 (Prime minister star). "
                        "Each star has Wu Xing element. "
                        "Safer to travel, more dangerous constellations.",
        "integration": "The 12 palaces map to BaZi pillars: "
                       "命宫=Day pillar, 父母宫=Year pillar, "
                       "兄弟宫=Month pillar. Can cross-validate.",
        "accident_death": "疾厄宫 (Health palace) + 迁移宫 (Travel palace) = "
                          "accident indicators. 杀破狼 pattern = violent change.",
    },
    "I Ching / Zhou Yi (周易)": {
        "origin": "China, ~3000 years",
        "commonality": "64 hexagrams from 8 trigrams. Each hexagram has "
                       "judgment, image, lines. Used for divination and philosophy.",
        "key_elements": "Each trigram has element: 乾=金, 坤=土, 震=木, "
                        "巽=木, 坎=水, 离=火, 艮=土, 兑=金.",
        "integration": "Can generate hexagram from BaZi year/month/day/hour. "
                       "Each pillar maps to a trigram. "
                       "Upper trigram = external, Lower = internal.",
        "accident_death": "Hexagram 29 (坎/Water) = danger, pitfall, death. "
                          "Hexagram 63 (既济) = completion, ending. "
                          "Line positions 3&4 (human realm) are critical.",
    },
    "Western Numerology (Pythagorean)": {
        "origin": "Greece, ~2500 years",
        "commonality": "Numbers 1-9 have archetypal meanings. "
                       "Life path number = destiny number in Chinese.",
        "key_elements": "Each number maps to a planet (1=Sun, 2=Moon, ...) "
                        "and element. Odd=Yang(masculine), Even=Yin(feminine).",
        "integration": "Already in core/western.py. Can add: "
                       "Expression number = 人格, Soul Urge = 内心.",
        "accident_death": "Personal Year number 4 or 8 = crisis years. "
                          "Pinnacle cycles = 大运 periods.",
    },
    "Tarot": {
        "origin": "Italy, ~1440 AD (modern form)",
        "commonality": "78 cards: 22 Major Arcana (archetypes) + 56 Minor "
                       "(4 suits). Each card has astrological/elemental correspondence.",
        "key_elements": "Wands=火/Fire, Cups=水/Water, Swords=风/Air, "
                        "Coins=土/Earth. Major Arcana = 大运 stages.",
        "integration": "Death card (XIII) = transformation, not physical death. "
                       "Tower (XVI) = sudden upheaval (accident). "
                       "Can be used for yearly readings.",
        "accident_death": "Tower + Death + 5 of Swords = accident. "
                          "3 of Swords = heartbreak, grief. "
                          "10 of Swords = painful ending.",
    },
    "Chinese 28 Mansions (二十八宿)": {
        "origin": "China, ~2000 years",
        "commonality": "28 lunar mansions divided into 4 groups (青龙/朱雀/白虎/玄武). "
                       "Each mansion governs specific life areas.",
        "key_elements": "East=木(青龙): 角亢氐房心尾箕. "
                        "South=火(朱雀): 井鬼柳星张翼轸. "
                        "West=金(白虎): 奎娄胃昴毕觜参. "
                        "North=水(玄武): 斗牛女虚危室壁.",
        "integration": "Birth day determines birth mansion. "
                       "Year's mansion = annual fortune. "
                       "Can add as refinement layer.",
        "accident_death": "Certain mansions bring death/accident: "
                          "鬼宿 (Ghost), 虚宿 (Void), 星宿 (Star - collapse).",
    },
    "Bazi / Four Pillars (八字)": {
        "origin": "China, Tang Dynasty ~700 AD",
        "commonality": "Already implemented in core/bazi.py.",
        "key_elements": "10 Heavenly Stems + 12 Earthly Branches = 60 cycle. "
                        "5 elements with Yin/Yang differentiation.",
        "integration": "Already integrated. Current improvements: "
                       "Qimen year analysis, death pattern detection.",
        "accident_death": "七杀攻身+羊刃倒戈+枭神夺食 = violent death. "
                          "印星死绝+比劫夺财 = mortal illness.",
    },
}

# Foreign approaches that can improve accuracy
FOREIGN_TECHNIQUES = {
    "Statistical Bayesian Calibration": {
        "source": "Modern data science",
        "use": "Weight fusion by historical accuracy. Already implemented in calibrator.py.",
        "improvement_potential": "High - more historical data = better weights",
    },
    "Survival Analysis (Kaplan-Meier)": {
        "source": "Medical statistics",
        "use": "Predict lifespan probability from element patterns. "
               "Already partially covered by lifespan formula.",
        "improvement_potential": "Medium - needs large dataset of known lifespans",
    },
    "Markov Chain Monte Carlo": {
        "source": "Bayesian statistics",
        "use": "Simulate possible life outcomes from BaZi patterns. "
               "Generate probability distributions for wealth/career/health.",
        "improvement_potential": "Medium - computationally intensive but powerful",
    },
    "Network Analysis (Social Graph)": {
        "source": "Sociology",
        "use": "Map BaZi compatibility networks. "
               "Who succeeds with whom, mentor relationships.",
        "improvement_potential": "Medium - needs relationship dataset",
    },
}


def print_reference():
    import json
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("    Foreign Divination Systems — Cross-Reference")
    print("=" * 60)
    for name, info in FOREIGN_SYSTEMS.items():
        print(f"\n{'='*40}")
        print(f"  {name}")
        print(f"{'='*40}")
        print(f"  起源: {info['origin']}")
        print(f"  共性: {info['commonality']}")
        print(f"  要素: {info['key_elements']}")
        print(f"  集成: {info['integration']}")
        print(f"  凶灾: {info['accident_death']}")

    print(f"\n\n{'='*60}")
    print("    Modern Techniques")
    print("=" * 60)
    for name, info in FOREIGN_TECHNIQUES.items():
        print(f"\n  {name}")
        print(f"    来源: {info['source']}")
        print(f"    用途: {info['use']}")
        print(f"    潜力: {info['improvement_potential']}")


if __name__ == "__main__":
    print_reference()
