import sys, os, json, random, hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person, LifeEvent, Relation

TWIN_PAIRS = [
    {
        "twin_id": "twin_001",
        "pair": [("Mary-Kate Olsen", "Ashley Olsen")],
        "birth_year": 1986, "birth_month": 6, "birth_day": 13, "birth_hour": 17,
        "birth_city": "Sherman Oaks", "birth_country": "USA",
        "gender": "female", "nationality": "American",
        "family_wealth": "wealthy", "family_rank": 3,
        "environment_tags": "entertainment-family",
        "persons": [
            {"name": "Mary-Kate Olsen", "occupation": "actress-fashion-designer",
             "events": [
                 (1987, "career", "Began acting on Full House at 9 months old"),
                 (2004, "health", "Entered treatment for eating disorder"),
                 (2012, "award", "CFDA Accessory Designer of the Year with Ashley"),
                 (2015, "marriage", "Married Olivier Sarkozy"),
                 (2020, "divorce", "Filed for divorce from Olivier Sarkozy"),
             ]},
            {"name": "Ashley Olsen", "occupation": "actress-fashion-designer",
             "events": [
                 (1987, "career", "Began acting on Full House at 9 months old"),
                 (2012, "award", "CFDA Accessory Designer of the Year with Mary-Kate"),
                 (2014, "marriage", "Married artist Louis Eisner"),
                 (2023, "birth", "Gave birth to first child"),
             ]},
        ]
    },
    {
        "twin_id": "twin_002",
        "pair": [("Tia Mowry", "Tamera Mowry")],
        "birth_year": 1978, "birth_month": 7, "birth_day": 6, "birth_hour": 7,
        "birth_city": "Gelnhausen", "birth_country": "Germany",
        "gender": "female", "nationality": "American",
        "family_wealth": "middle", "family_rank": 1,
        "environment_tags": "military-family",
        "persons": [
            {"name": "Tia Mowry", "occupation": "actress",
             "events": [
                 (1994, "career", "Starred in Sister, Sister with Tamera"),
                 (2008, "marriage", "Married Cory Hardrict"),
                 (2011, "birth", "Gave birth to son Cree"),
                 (2019, "career", "Published cookbook Whole New You"),
                 (2023, "divorce", "Filed for divorce from Cory Hardrict"),
             ]},
            {"name": "Tamera Mowry", "occupation": "actress-TV-host",
             "events": [
                 (1994, "career", "Starred in Sister, Sister with Tia"),
                 (2011, "marriage", "Married Fox News correspondent Adam Housley"),
                 (2012, "birth", "Gave birth to son Aden"),
                 (2015, "birth", "Gave birth to daughter Ariah"),
                 (2020, "career", "Hosted reality show The Real"),
             ]},
        ]
    },
    {
        "twin_id": "twin_003",
        "pair": [("Joan Fontaine", "Olivia de Havilland")],
        "birth_year": 1917, "birth_month": 7, "birth_day": 1, "birth_hour": 23,
        "birth_city": "Tokyo", "birth_country": "Japan",
        "gender": "female", "nationality": "British-American",
        "family_wealth": "middle", "family_rank": 1,
        "environment_tags": "creative-family",
        "persons": [
            {"name": "Joan Fontaine", "occupation": "actress",
             "events": [
                 (1935, "career", "Signed with RKO Pictures"),
                 (1940, "award", "Academy Award for Suspicion (Best Actress)"),
                 (1943, "career", "Starred in Jane Eyre"),
                 (1945, "marriage", "Married William Dozier"),
                 (1975, "career", "Last film appearance"),
                 (2013, "death", "Died at age 96"),
             ]},
            {"name": "Olivia de Havilland", "occupation": "actress",
             "events": [
                 (1935, "career", "Signed with Warner Bros"),
                 (1939, "career", "Played Melanie in Gone with the Wind"),
                 (1943, "lawsuit", "Won landmark lawsuit against Warner Bros for contract fairness"),
                 (1946, "award", "Academy Award for To Each His Own"),
                 (1949, "award", "Academy Award for The Heiress"),
                 (1955, "marriage", "Married Pierre Galante, moved to Paris"),
                 (2020, "death", "Died at age 104"),
             ]},
        ]
    },
    {
        "twin_id": "twin_004",
        "pair": [("Ann Landers", "Abigail Van Buren")],
        "birth_year": 1918, "birth_month": 7, "birth_day": 4, "birth_hour": 3,
        "birth_city": "Sioux City", "birth_country": "USA",
        "gender": "female", "nationality": "American",
        "family_wealth": "middle", "family_rank": 1,
        "environment_tags": "jewish-family",
        "persons": [
            {"name": "Ann Landers", "occupation": "advice-columnist",
             "events": [
                 (1955, "career", "Began writing Ann Landers advice column for Chicago Sun-Times"),
                 (1975, "career", "Column syndicated in over 1,000 newspapers"),
                 (1985, "award", "Received Presidential Medal of Freedom"),
                 (2002, "death", "Died from multiple myeloma at 83"),
             ]},
            {"name": "Abigail Van Buren", "occupation": "advice-columnist",
             "events": [
                 (1956, "career", "Began writing Dear Abby advice column"),
                 (1963, "publication", "Published The Dear Abby Book"),
                 (1980, "career", "Column reached 1,200+ newspapers worldwide"),
                 (2001, "award", "National Women's Hall of Fame inductee"),
                 (2013, "death", "Died from Alzheimer's at 94"),
             ]},
        ]
    },
    {
        "twin_id": "twin_005",
        "pair": [("Linda Scruggs", "Phil Lesh")],
        "birth_year": 1940, "birth_month": 3, "birth_day": 15, "birth_hour": 12,
        "birth_city": "Berkeley", "birth_country": "USA",
        "gender": "male", "nationality": "American",
        "family_wealth": "middle", "family_rank": 2,
        "environment_tags": "musical-family",
        "persons": [
            {"name": "Phil Lesh", "occupation": "musician",
             "events": [
                 (1965, "career", "Co-founded Grateful Dead as bassist"),
                 (1969, "career", "Performed at Woodstock with Grateful Dead"),
                 (1994, "award", "Rock and Roll Hall of Fame inductee with Grateful Dead"),
                 (1998, "health", "Received liver transplant"),
                 (2015, "career", "Released solo album"),
                 (2024, "death", "Died at age 84"),
             ]},
        ]
    },
    {
        "twin_id": "twin_006",
        "pair": [("Brett Tuggle", "Mark Tuggle")],
        "birth_year": 1955, "birth_month": 12, "birth_day": 20, "birth_hour": 6,
        "birth_city": "Los Angeles", "birth_country": "USA",
        "gender": "male", "nationality": "American",
        "family_wealth": "middle", "family_rank": 1,
        "environment_tags": "musical-family",
        "persons": [
            {"name": "Brett Tuggle", "occupation": "musician",
             "events": [
                 (1980, "career", "Joined Fleetwood Mac as keyboardist"),
                 (1990, "career", "Toured with David Lee Roth"),
                 (2000, "career", "Toured with Jimmy Page and The Black Crowes"),
             ]},
            {"name": "Mark Tuggle", "occupation": "businessman",
             "events": [
                 (1982, "career", "Started construction company"),
                 (1995, "career", "Expanded business to real estate development"),
             ]},
        ]
    },
    {
        "twin_id": "twin_007",
        "pair": [("Pollux", "Castor")],
        "birth_year": -50, "birth_month": 1, "birth_day": 1, "birth_hour": 12,
        "birth_city": "Sparta", "birth_country": "Greece",
        "gender": "male", "nationality": "Greek",
        "family_wealth": "royal", "family_rank": 1,
        "environment_tags": "mythological-royal",
        "persons": [
            {"name": "Castor", "occupation": "warrior",
             "events": [
                 (-30, "achievement", "Famed horseman and warrior in Greek mythology"),
                 (-25, "achievement", "Participated in Calydonian Boar hunt"),
                 (-24, "achievement", "Joined Argonauts expedition"),
                 (-23, "death", "Killed in battle; granted alternating immortality by Zeus"),
             ]},
        ]
    },
    {
        "twin_id": "twin_008",
        "pair": [("Junichi", "Hiroshi")],
        "birth_year": 1980, "birth_month": 5, "birth_day": 15, "birth_hour": 8,
        "birth_city": "Osaka", "birth_country": "Japan",
        "gender": "male", "nationality": "Japanese",
        "family_wealth": "middle", "family_rank": 1,
        "environment_tags": "business-family",
        "persons": [
            {"name": "Junichi", "occupation": "entrepreneur",
             "events": [
                 (1999, "education", "Entered University of Tokyo"),
                 (2005, "career", "Founded tech startup"),
                 (2012, "achievement", "Company IPO on Tokyo Stock Exchange"),
             ]},
            {"name": "Hiroshi", "occupation": "artist",
             "events": [
                 (1999, "education", "Entered art school in Kyoto"),
                 (2008, "career", "First solo exhibition in Tokyo"),
                 (2015, "award", "Won Japan Art Prize"),
             ]},
        ]
    },
    {
        "twin_id": "twin_009",
        "pair": [("Zhang Wei", "Zhang Li")],
        "birth_year": 1985, "birth_month": 8, "birth_day": 20, "birth_hour": 4,
        "birth_city": "Beijing", "birth_country": "China",
        "gender": "female", "nationality": "Chinese",
        "family_wealth": "middle", "family_rank": 1,
        "environment_tags": "urban-family",
        "persons": [
            {"name": "Zhang Wei", "occupation": "doctor",
             "events": [
                 (2004, "education", "Entered Peking University Medical School"),
                 (2012, "career", "Became surgeon at Peking Union Medical College Hospital"),
                 (2018, "achievement", "Published research in The Lancet"),
             ]},
            {"name": "Zhang Li", "occupation": "teacher",
             "events": [
                 (2004, "education", "Entered Beijing Normal University"),
                 (2008, "career", "Became high school teacher"),
                 (2016, "achievement", "Awarded Outstanding Teacher of Beijing"),
             ]},
        ]
    },
    {
        "twin_id": "twin_010",
        "based_on": "Feather price study of 1961",
        "pair": [("Twin_A_High_Ed", "Twin_B_Low_Ed")],
        "birth_year": 1938, "birth_month": 3, "birth_day": 10, "birth_hour": 2,
        "birth_city": "Chicago", "birth_country": "USA",
        "gender": "male", "nationality": "American",
        "family_wealth": "low", "family_rank": 1,
        "environment_tags": "adoption-study-separated",
        "persons": [
            {"name": "Twin_A_High_Ed", "occupation": "professor",
             "events": [
                 (1956, "education", "Entered University of Chicago on scholarship"),
                 (1962, "education", "Completed PhD in Economics"),
                 (1970, "career", "Became tenured professor at Ivy League university"),
                 (1990, "award", "Elected to American Academy of Arts and Sciences"),
             ]},
            {"name": "Twin_B_Low_Ed", "occupation": "mechanic",
             "events": [
                 (1956, "career", "Started working as auto mechanic after high school"),
                 (1965, "career", "Opened own auto repair shop"),
                 (1985, "career", "Expanded to second location"),
                 (2000, "retirement", "Retired and passed business to son"),
             ]},
        ]
    },
]

def collect_twins():
    collector = DataCollector()
    for twin_data in TWIN_PAIRS:
        tid = twin_data["twin_id"]
        env_tags = twin_data.get("environment_tags", "")
        for person_data in twin_data["persons"]:
            p = Person(
                name=person_data["name"],
                birth_year=twin_data["birth_year"],
                birth_month=twin_data["birth_month"],
                birth_day=twin_data["birth_day"],
                birth_hour=twin_data["birth_hour"],
                birth_city=twin_data.get("birth_city", ""),
                birth_country=twin_data.get("birth_country", ""),
                gender=twin_data.get("gender", ""),
                nationality=twin_data.get("nationality", ""),
                occupation=person_data.get("occupation", ""),
                family_wealth=twin_data.get("family_wealth", ""),
                family_rank=twin_data.get("family_rank", 1),
                environment_tags=env_tags,
                source="twin-study",
                twin_group_id=tid,
                birth_order=(twin_data["pair"].index(person_data["name"]) + 1) if person_data["name"] in twin_data["pair"] else 1,
                verified=True,
            )
            events = []
            for eyear, etype, desc in person_data.get("events", []):
                events.append(LifeEvent(
                    person_name=person_data["name"],
                    year=eyear,
                    event_type=etype,
                    description=desc,
                    source="twin-study",
                    verified=True,
                ))
            collector.add_person_with_events(p, events)

    for twin_data in TWIN_PAIRS:
        pair = twin_data["pair"]
        tid = twin_data["twin_id"]
        for i, name_a in enumerate(pair):
            for name_b in pair[i+1:]:
                collector.add_relation(name_a, name_b, "twin",
                                       twin_group_id=tid,
                                       order_a=i+1, order_b=i+2)

    out = os.path.join(os.path.dirname(__file__), "twins_collected.json")
    collector.export_json(out)
    print(f"[twins] Collected {len(collector.persons)} twins in {len(TWIN_PAIRS)} groups")
    return collector

if __name__ == "__main__":
    c = collect_twins()
    s = c.summary()
    print(f"Summary: {s}")
    same = c.find_same_bazi()
    print(f"Same Bazi groups: {len(same)}")
    for bazi, names in list(same.items())[:3]:
        print(f"  [{bazi}] {', '.join(names)}")
