import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from collector import DataCollector, Person, LifeEvent

PERSONS_DATA = [
    {
        "name": "Albert Einstein",
        "birth_year": 1879, "birth_month": 3, "birth_day": 14,
        "death_year": 1955, "death_month": 4, "death_day": 18,
        "nationality": "German-American", "occupation": "scientist", "category": "celebrity",
        "events": [
            {"year": 1896, "event_type": "education", "description": "Enrolled at ETH Zurich"},
            {"year": 1905, "event_type": "achievement", "description": "Published Annus Mirabilis papers (photoelectric effect, Brownian motion, special relativity, E=mc²)"},
            {"year": 1915, "event_type": "achievement", "description": "Completed general theory of relativity"},
            {"year": 1921, "event_type": "award", "description": "Nobel Prize in Physics for photoelectric effect"},
            {"year": 1933, "event_type": "migration", "description": "Fled Nazi Germany, emigrated to United States"},
            {"year": 1939, "event_type": "political", "description": "Signed letter to President Roosevelt warning of Nazi atomic bomb potential"},
            {"year": 1955, "event_type": "death", "description": "Died at Princeton Hospital at age 76"},
        ]
    },
    {
        "name": "Isaac Newton",
        "birth_year": 1643, "birth_month": 1, "birth_day": 4,
        "death_year": 1727, "death_month": 3, "death_day": 31,
        "nationality": "English", "occupation": "scientist", "category": "celebrity",
        "events": [
            {"year": 1661, "event_type": "education", "description": "Entered Trinity College, Cambridge"},
            {"year": 1666, "event_type": "achievement", "description": "Developed calculus, laws of motion, and universal gravitation during Annus Mirabilis"},
            {"year": 1687, "event_type": "publication", "description": "Published Philosophiæ Naturalis Principia Mathematica"},
            {"year": 1703, "event_type": "position", "description": "Elected President of the Royal Society"},
            {"year": 1705, "event_type": "award", "description": "Knighted by Queen Anne, first scientist to receive knighthood"},
        ]
    },
    {
        "name": "Marie Curie",
        "birth_year": 1867, "birth_month": 11, "birth_day": 7,
        "death_year": 1934, "death_month": 7, "death_day": 4,
        "nationality": "Polish-French", "occupation": "scientist", "category": "celebrity",
        "events": [
            {"year": 1891, "event_type": "education", "description": "Moved to Paris to study at Sorbonne"},
            {"year": 1898, "event_type": "discovery", "description": "Discovered polonium and radium"},
            {"year": 1903, "event_type": "award", "description": "Nobel Prize in Physics (shared with Becquerel and Pierre Curie)"},
            {"year": 1911, "event_type": "award", "description": "Nobel Prize in Chemistry for radium and polonium isolation"},
            {"year": 1914, "event_type": "position", "description": "Founded Radium Institute in Paris"},
            {"year": 1934, "event_type": "death", "description": "Died of aplastic anemia from radiation exposure"},
        ]
    },
    {
        "name": "Leonardo da Vinci",
        "birth_year": 1452, "birth_month": 4, "birth_day": 15,
        "death_year": 1519, "death_month": 5, "death_day": 2,
        "nationality": "Italian", "occupation": "artist", "category": "celebrity",
        "events": [
            {"year": 1466, "event_type": "education", "description": "Apprenticed to Andrea del Verrocchio in Florence"},
            {"year": 1482, "event_type": "migration", "description": "Moved to Milan to work for Duke Ludovico Sforza"},
            {"year": 1495, "event_type": "creation", "description": "Began painting The Last Supper"},
            {"year": 1503, "event_type": "creation", "description": "Began painting the Mona Lisa"},
            {"year": 1508, "event_type": "study", "description": "Conducted anatomical studies and dissections"},
        ]
    },
    {
        "name": "Wolfgang Amadeus Mozart",
        "birth_year": 1756, "birth_month": 1, "birth_day": 27,
        "death_year": 1791, "death_month": 12, "death_day": 5,
        "nationality": "Austrian", "occupation": "artist", "category": "celebrity",
        "events": [
            {"year": 1762, "event_type": "performance", "description": "First European tour as child prodigy with sister Nannerl"},
            {"year": 1781, "event_type": "migration", "description": "Moved to Vienna, began independent career"},
            {"year": 1786, "event_type": "creation", "description": "Premiered The Marriage of Figaro"},
            {"year": 1787, "event_type": "creation", "description": "Premiered Don Giovanni"},
            {"year": 1791, "event_type": "creation", "description": "Completed Requiem Mass in D minor (unfinished)"},
        ]
    },
    {
        "name": "Confucius",
        "birth_year": -551, "birth_month": 9, "birth_day": 28,
        "death_year": -479, "death_month": 4, "death_day": 11,
        "nationality": "Chinese", "occupation": "philosopher", "category": "celebrity",
        "events": [
            {"year": -531, "event_type": "position", "description": "Appointed Governor of Zhongdu (Central Capital)"},
            {"year": -517, "event_type": "migration", "description": "Began 14-year journey through Chinese states seeking virtuous rulers"},
            {"year": -484, "event_type": "education", "description": "Returned to Lu, devoted to teaching and editing classics"},
            {"year": -479, "event_type": "death", "description": "Died at age 72, mourned by disciples who compiled The Analects"},
        ]
    },
    {
        "name": "Sima Qian",
        "birth_year": -145, "birth_month": 1, "birth_day": 1,
        "death_year": -86, "death_month": 1, "death_day": 1,
        "nationality": "Chinese", "occupation": "writer", "category": "celebrity",
        "events": [
            {"year": -110, "event_type": "position", "description": "Succeeded father Sima Tan as Grand Historian of Han"},
            {"year": -99, "event_type": "trial", "description": "Imprisoned and castrated for defending General Li Ling"},
            {"year": -96, "event_type": "achievement", "description": "Resumed historical writing after release from prison"},
            {"year": -91, "event_type": "publication", "description": "Completed Records of the Grand Historian (Shiji), 130 chapters"},
        ]
    },
    {
        "name": "Li Bai",
        "birth_year": 701, "birth_month": 5, "birth_day": 19,
        "death_year": 762, "death_month": 12, "death_day": 1,
        "nationality": "Chinese", "occupation": "writer", "category": "celebrity",
        "events": [
            {"year": 724, "event_type": "migration", "description": "Left Shu (Sichuan) to journey along the Yangtze River"},
            {"year": 742, "event_type": "position", "description": "Summoned to Chang'an, appointed at Hanlin Academy"},
            {"year": 744, "event_type": "migration", "description": "Left Chang'an, became wandering poet; met Du Fu"},
            {"year": 756, "event_type": "political", "description": "Joined Prince Yong's rebellion against Emperor Suzong"},
            {"year": 758, "event_type": "trial", "description": "Exiled to Yelang but pardoned en route"},
        ]
    },
    {
        "name": "Nikola Tesla",
        "birth_year": 1856, "birth_month": 7, "birth_day": 10,
        "death_year": 1943, "death_month": 1, "death_day": 7,
        "nationality": "Serbian-American", "occupation": "scientist", "category": "celebrity",
        "events": [
            {"year": 1882, "event_type": "discovery", "description": "Conceived rotating magnetic field principle"},
            {"year": 1888, "event_type": "patent", "description": "Patented alternating current motor and polyphase system"},
            {"year": 1891, "event_type": "invention", "description": "Invented Tesla coil"},
            {"year": 1899, "event_type": "experiment", "description": "Built Colorado Springs experimental station"},
            {"year": 1915, "event_type": "lawsuit", "description": "Marconi awarded Nobel Prize despite using Tesla's patented radio technology"},
        ]
    },
    {
        "name": "Ludwig van Beethoven",
        "birth_year": 1770, "birth_month": 12, "birth_day": 17,
        "death_year": 1827, "death_month": 3, "death_day": 26,
        "nationality": "German", "occupation": "artist", "category": "celebrity",
        "events": [
            {"year": 1787, "event_type": "education", "description": "Traveled to Vienna to study with Mozart"},
            {"year": 1792, "event_type": "migration", "description": "Permanently moved to Vienna to study with Haydn"},
            {"year": 1801, "event_type": "health", "description": "Realized his hearing loss was incurable"},
            {"year": 1804, "event_type": "creation", "description": "Composed Symphony No. 3 (Eroica)"},
            {"year": 1824, "event_type": "creation", "description": "Premiered Symphony No. 9 (Choral) completely deaf"},
        ]
    },
]

def seed():
    collector = DataCollector()
    for pd in PERSONS_DATA:
        person = Person(
            name=pd["name"],
            birth_year=pd["birth_year"],
            birth_month=pd["birth_month"],
            birth_day=pd["birth_day"],
            death_year=pd.get("death_year"),
            death_month=pd.get("death_month"),
            death_day=pd.get("death_day"),
            nationality=pd.get("nationality", ""),
            occupation=pd.get("occupation", ""),
            category="celebrity",
            source="verified-seed",
            verified=True,
        )
        events = [
            LifeEvent(
                person_name=pd["name"],
                year=e["year"],
                event_type=e["event_type"],
                description=e["description"],
                source="verified-seed",
                verified=True,
            )
            for e in pd.get("events", [])
        ]
        collector.add_person_with_events(person, events)

    out_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    collector.export_json(out_path)
    print(f"[seed] Seeded {len(PERSONS_DATA)} persons with verified life events")
    return collector

if __name__ == "__main__":
    seed()
