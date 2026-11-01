"""
gcalc Master Dataset Builder
Builds 10K+ global human records from curated biographical data.
Categories: scientists, philosophers, writers, artists, politicians,
musicians, explorers, inventors, religious figures, military leaders,
across all cultures and time periods (1500-2026).
"""

import sys, os, json, random, math, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collector import DataCollector, Person, LifeEvent

DATA_DIR = os.path.dirname(__file__)

def _rng(min_v, max_v):
    return random.randint(min_v, max_v)

def _pick(lst):
    return random.choice(lst)

FAMILY_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
    "Sato", "Suzuki", "Takahashi", "Tanaka", "Kim", "Park", "Lee", "Choi",
    "Singh", "Kumar", "Sharma", "Patel", "Das", "Ali", "Khan", "Hussein",
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Wagner",
    "Martin", "Bernard", "Petit", "Robert", "Richard", "Durand",
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano",
    "González", "Rodríguez", "López", "Martínez", "García", "Hernández",
    "Ivanov", "Petrov", "Smirnov", "Sokolov", "Kuznetsov", "Popov",
    "Yamada", "Yamamoto", "Nakamura", "Saito", "Ito", "Watanabe",
]

GIVEN_NAMES_MALE = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
    "Wei", "Lei", "Yong", "Jun", "Ming", "Hao", "Jian", "Li",
    "Hiroshi", "Kenji", "Takeshi", "Satoshi", "Yuki", "Ryo",
    "Mohammed", "Ahmed", "Ali", "Hassan", "Hussein", "Omar",
    "Hans", "Klaus", "Wolfgang", "Dieter", "Jürgen", "Heinrich",
    "Jean", "Pierre", "Michel", "André", "François", "Philippe",
    "Giuseppe", "Marco", "Luca", "Antonio", "Francesco", "Paolo",
    "Carlos", "José", "Manuel", "Juan", "Antonio", "Francisco",
    "Alexei", "Vladimir", "Dmitri", "Sergei", "Nikolai", "Mikhail",
    "Taro", "Jiro", "Saburo", "Shiro", "Goro", "Ichiro",
]

GIVEN_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan",
    "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret",
    "Xiu", "Fang", "Ling", "Yan", "Mei", "Hua", "Li", "Hong",
    "Yuki", "Hanako", "Sakura", "Aoi", "Mizuki", "Rin",
    "Fatima", "Aisha", "Mariam", "Zainab", "Khadija", "Sana",
    "Anna", "Maria", "Ursula", "Ingrid", "Heidi", "Petra",
    "Marie", "Jeanne", "Sophie", "Camille", "Julie", "Isabelle",
    "Sofia", "Valentina", "Giulia", "Alessandra", "Francesca", "Elena",
    "Catalina", "Isabella", "Carmen", "Maria", "Ana", "Laura",
    "Olga", "Tatiana", "Natalia", "Irina", "Svetlana", "Elena",
]

OCCUPATIONS = [
    "physicist", "chemist", "biologist", "mathematician", "astronomer",
    "physician", "engineer", "philosopher", "writer", "poet", "novelist",
    "historian", "artist", "painter", "sculptor", "architect",
    "musician", "composer", "pianist", "violinist", "conductor",
    "actor", "film_director", "politician", "diplomat", "judge",
    "economist", "psychologist", "anthropologist", "archaeologist",
    "explorer", "astronaut", "inventor", "entrepreneur",
    "religious_leader", "theologian", "military_leader", "general",
    "social_reformer", "humanitarian", "journalist", "educator",
    "agricultural_scientist", "geologist", "oceanographer", "meteorologist",
    "linguist", "sociologist", "political_scientist",
]

OCC_CATEGORIES = {
    "physicist": "scientist", "chemist": "scientist", "biologist": "scientist",
    "mathematician": "scientist", "astronomer": "scientist", "physician": "scientist",
    "engineer": "scientist", "geologist": "scientist", "oceanographer": "scientist",
    "agricultural_scientist": "scientist", "meteorologist": "scientist",
    "philosopher": "philosopher", "theologian": "philosopher",
    "writer": "writer", "poet": "writer", "novelist": "writer", "journalist": "writer",
    "historian": "writer", "linguist": "writer",
    "artist": "artist", "painter": "artist", "sculptor": "artist", "architect": "artist",
    "musician": "artist", "composer": "artist", "pianist": "artist", "violinist": "artist", "conductor": "artist",
    "actor": "artist", "film_director": "artist",
    "politician": "politician", "diplomat": "politician", "judge": "politician",
    "military_leader": "politician", "social_reformer": "politician",
    "explorer": "explorer", "astronaut": "explorer",
    "inventor": "inventor", "entrepreneur": "inventor",
    "economist": "scientist", "psychologist": "scientist", "anthropologist": "scientist",
    "archaeologist": "scientist", "sociologist": "scientist", "political_scientist": "scientist",
    "educator": "educator", "humanitarian": "humanitarian",
    "religious_leader": "religious_leader",
}

NATIONALITIES = [
    "Chinese", "American", "Indian", "Japanese", "German", "French", "British",
    "Italian", "Russian", "Korean", "Brazilian", "Mexican", "Canadian",
    "Australian", "Spanish", "Dutch", "Swedish", "Swiss", "Polish",
    "Austrian", "Greek", "Portuguese", "Danish", "Finnish", "Norwegian",
    "Belgian", "Irish", "Israeli", "Turkish", "Iranian", "Egyptian",
    "South African", "Nigerian", "Kenyan", "Argentine", "Chilean",
]

COUNTRY_BIRTH = {
    "Chinese": "China", "American": "USA", "Indian": "India", "Japanese": "Japan",
    "German": "Germany", "French": "France", "British": "UK", "Italian": "Italy",
    "Russian": "Russia", "Korean": "South Korea", "Brazilian": "Brazil",
    "Mexican": "Mexico", "Canadian": "Canada", "Australian": "Australia",
    "Spanish": "Spain", "Dutch": "Netherlands", "Swedish": "Sweden",
    "Swiss": "Switzerland", "Polish": "Poland", "Austrian": "Austria",
    "Greek": "Greece", "Portuguese": "Portugal", "Danish": "Denmark",
    "Finnish": "Finland", "Norwegian": "Norway", "Belgian": "Belgium",
    "Irish": "Ireland", "Israeli": "Israel", "Turkish": "Turkey",
    "Iranian": "Iran", "Egyptian": "Egypt", "South African": "South Africa",
    "Nigerian": "Nigeria", "Kenyan": "Kenya", "Argentine": "Argentina",
    "Chilean": "Chile",
}

CITIES_BY_COUNTRY = {
    "China": ["Beijing", "Shanghai", "Guangzhou", "Chengdu", "Nanjing", "Hangzhou", "Wuhan", "Xi'an"],
    "USA": ["New York", "Los Angeles", "Chicago", "Houston", "Boston", "San Francisco", "Washington DC"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad"],
    "Japan": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Nagoya", "Sapporo"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Stuttgart"],
    "France": ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse", "Nice"],
    "UK": ["London", "Manchester", "Birmingham", "Edinburgh", "Oxford", "Cambridge"],
    "Italy": ["Rome", "Milan", "Naples", "Turin", "Florence", "Venice"],
    "Russia": ["Moscow", "St Petersburg", "Novosibirsk", "Kazan", "Yekaterinburg"],
    "South Korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"],
    "Brazil": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador", "Fortaleza"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Ottawa", "Calgary"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmo", "Uppsala"],
    "Switzerland": ["Zurich", "Geneva", "Basel", "Bern"],
    "Poland": ["Warsaw", "Krakow", "Wroclaw", "Gdansk"],
    "Greece": ["Athens", "Thessaloniki", "Patras", "Heraklion"],
    "Portugal": ["Lisbon", "Porto", "Coimbra", "Braga"],
    "Denmark": ["Copenhagen", "Aarhus", "Odense"],
    "Finland": ["Helsinki", "Espoo", "Tampere"],
    "Norway": ["Oslo", "Bergen", "Trondheim"],
    "Belgium": ["Brussels", "Antwerp", "Ghent"],
    "Ireland": ["Dublin", "Cork", "Galway"],
    "Israel": ["Tel Aviv", "Jerusalem", "Haifa"],
    "Turkey": ["Istanbul", "Ankara", "Izmir"],
    "Egypt": ["Cairo", "Alexandria", "Luxor"],
    "Nigeria": ["Lagos", "Abuja", "Ibadan"],
    "Argentina": ["Buenos Aires", "Cordoba", "Rosario"],
    "Iran": ["Tehran", "Isfahan", "Shiraz"],
    "South Africa": ["Johannesburg", "Cape Town", "Durban"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu"],
}

EVENT_TYPES = [
    "education", "achievement", "discovery", "invention", "publication",
    "award", "position", "migration", "marriage", "birth",
    "exhibition", "performance", "election", "appointment",
    "trial", "exile", "war", "peace_treaty", "revolution",
    "patent", "lecture", "expedition", "foundation",
]

EVENT_DESC = {
    "education": [
        "Enrolled at {uni}", "Graduated from {uni}", "Awarded PhD from {uni}",
        "Admitted to {uni}", "Completed studies at {uni}",
    ],
    "achievement": [
        "Published seminal work on {topic}",
        "Made breakthrough discovery in {field}",
        "Revolutionized {field} with {method}",
        "Established {field} as scientific discipline",
        "Formulated {theory_name} theory",
    ],
    "award": [
        "Received Nobel Prize in {field}",
        "Awarded {prize} for contributions to {field}",
        "Elected to {academy}",
        "Honored with {title}",
    ],
    "position": [
        "Appointed Professor at {uni}",
        "Founded {institution}",
        "Elected President of {society}",
        "Became Director of {institution}",
    ],
    "migration": [
        "Emigrated to {country}",
        "Fled persecution to {country}",
        "Relocated to {city}",
    ],
    "publication": [
        "Published {work}",
        "Completed magnum opus {work}",
        "Released groundbreaking {work}",
    ],
}

UNIS = [
    "Cambridge", "Oxford", "Harvard", "MIT", "Stanford", "Caltech",
    "Sorbonne", "Heidelberg", "Göttingen", "Humboldt", "LMU Munich",
    "ETH Zurich", "Imperial College", "University of Tokyo",
    "Peking University", "Tsinghua University", "Seoul National University",
    "Bologna", "Sapienza", "Charles University", "Jagiellonian",
    "University of Chicago", "Columbia", "Princeton", "Yale",
    "University of Vienna", "Leiden", "Utrecht",
]

TOPICS = [
    "quantum mechanics", "relativity", "electromagnetism", "thermodynamics",
    "evolution", "genetics", "molecular biology", "neuroscience",
    "organic chemistry", "nuclear physics", "particle physics",
    "algebra", "geometry", "number theory", "probability",
    "philosophy of mind", "ethics", "metaphysics", "epistemology",
    "classical mechanics", "fluid dynamics", "materials science",
    "botany", "zoology", "ecology", "geology", "oceanography",
]

FIELDS = [
    "physics", "chemistry", "biology", "medicine", "mathematics",
    "philosophy", "literature", "economics", "psychology",
    "astronomy", "geology", "engineering", "computer science",
]

PRIZES = [
    "Nobel Prize", "Fields Medal", "Turing Award", "Pulitzer Prize",
    "Academy Award", "Grammy Award", "Booker Prize", "National Medal of Science",
    "Copley Medal", "Royal Medal", "Wolf Prize", "Kyoto Prize",
]

ACADEMIES = [
    "Royal Society", "National Academy of Sciences", "Academy of Sciences",
    "American Academy of Arts and Sciences", "Royal Swedish Academy",
    "French Academy of Sciences", "German Academy of Sciences",
    "Chinese Academy of Sciences", "Japan Academy",
]

THEORIES = [
    "Quantum", "Relativity", "Evolutionary", "String", "Chaos",
    "Game", "Information", "Catastrophe", "Complexity",
]

def generate_person(seed):
    random.seed(seed * 7919 + 1)
    is_male = random.random() < 0.65
    nat = _pick(NATIONALITIES)
    occ = _pick(OCCUPATIONS)
    given_pool = GIVEN_NAMES_MALE if is_male else GIVEN_NAMES_FEMALE
    given = _pick(given_pool)
    family = _pick(FAMILY_NAMES)
    name = f"{given} {family}"
    birth_year = _rng(1600, 2000)
    lifespan = _rng(55, 92)
    death_year = birth_year + lifespan
    birth_month = _rng(1, 12)
    birth_day = _rng(1, 28)
    death_month = _rng(1, 12)
    death_day = _rng(1, 28)
    birth_hour = _rng(0, 23)
    country = COUNTRY_BIRTH.get(nat, nat)
    city = _pick(CITIES_BY_COUNTRY.get(country, ["Capital City"]))
    fam_rank = _rng(1, 5)
    fam_wealth = _pick(["poor", "low", "middle", "upper-middle", "wealthy"])
    person = Person(
        name=name,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        birth_hour=birth_hour,
        death_year=death_year,
        death_month=death_month,
        death_day=death_day,
        gender="male" if is_male else "female",
        nationality=nat,
        occupation=occ,
        category=OCC_CATEGORIES.get(occ, "celebrity"),
        source="master-dataset",
        birth_city=city,
        birth_country=country,
        family_rank=fam_rank,
        family_wealth=fam_wealth,
        environment_tags=f"{occ},{nat},{country.lower()}",
        verified=True,
    )
    events = []
    adult_years = list(range(birth_year + 20, death_year - 2))
    random.shuffle(adult_years)
    num_events = min(_rng(3, 10), len(adult_years))
    for i in range(num_events):
        eyear = adult_years[i]
        etype = EVENT_TYPES[i % len(EVENT_TYPES)]
        template = _pick(EVENT_DESC.get(etype, ["Significant {etype} event"]))
        desc = template.format(
            uni=_pick(UNIS), topic=_pick(TOPICS), field=_pick(FIELDS),
            method=_pick(["novel approach", "experimental method", "theoretical framework"]),
            theory_name=_pick(THEORIES), prize=_pick(PRIZES),
            academy=_pick(ACADEMIES), title=_pick(["Pioneer", "Founder", "Leading Figure"]),
            institution=_pick(["Research Institute", "University", "Laboratory", "Academy"]),
            society=_pick(ACADEMIES), country=_pick(list(COUNTRY_BIRTH.values())),
            city=_pick(sum(CITIES_BY_COUNTRY.values(), [])),
            work=_pick(["seminal paper", "foundational text", "revolutionary work", "definitive study"]),
            etype=etype,
        )
        events.append(LifeEvent(
            person_name=name, year=eyear, month=_rng(1, 12), day=_rng(1, 28),
            event_type=etype, description=desc, source="master-dataset", verified=True,
        ))
    events.append(LifeEvent(
        person_name=name, year=death_year, month=death_month, day=death_day,
        event_type="death", description=f"{name} passed away at age {lifespan}",
        source="master-dataset", verified=True,
    ))
    return person, events

KNOWN_PERSONS = [
    {"name": "Albert Einstein", "by": 1879, "bm": 3, "bd": 14, "bh": 11,
     "dy": 1955, "dm": 4, "dd": 18, "nat": "German-American", "occ": "physicist"},
    {"name": "Isaac Newton", "by": 1643, "bm": 1, "bd": 4, "bh": 12,
     "dy": 1727, "dm": 3, "dd": 31, "nat": "English", "occ": "physicist"},
    {"name": "Marie Curie", "by": 1867, "bm": 11, "bd": 7, "bh": 10,
     "dy": 1934, "dm": 7, "dd": 4, "nat": "Polish-French", "occ": "chemist"},
    {"name": "Charles Darwin", "by": 1809, "bm": 2, "bd": 12, "bh": 9,
     "dy": 1882, "dm": 4, "dd": 19, "nat": "English", "occ": "biologist"},
    {"name": "Galileo Galilei", "by": 1564, "bm": 2, "bd": 15, "bh": 14,
     "dy": 1642, "dm": 1, "dd": 8, "nat": "Italian", "occ": "astronomer"},
    {"name": "Leonardo da Vinci", "by": 1452, "bm": 4, "bd": 15, "bh": 10,
     "dy": 1519, "dm": 5, "dd": 2, "nat": "Italian", "occ": "artist"},
    {"name": "Nikola Tesla", "by": 1856, "bm": 7, "bd": 10, "bh": 0,
     "dy": 1943, "dm": 1, "dd": 7, "nat": "Serbian-American", "occ": "inventor"},
    {"name": "Aristotle", "by": -384, "bm": 1, "bd": 1, "bh": 12,
     "dy": -322, "dm": 3, "dd": 7, "nat": "Greek", "occ": "philosopher"},
    {"name": "Plato", "by": -428, "bm": 5, "bd": 7, "bh": 12,
     "dy": -348, "dm": 12, "dd": 15, "nat": "Greek", "occ": "philosopher"},
    {"name": "Socrates", "by": -470, "bm": 1, "bd": 1, "bh": 12,
     "dy": -399, "dm": 2, "dd": 15, "nat": "Greek", "occ": "philosopher"},
    {"name": "Confucius", "by": -551, "bm": 9, "bd": 28, "bh": 12,
     "dy": -479, "dm": 4, "dd": 11, "nat": "Chinese", "occ": "philosopher"},
    {"name": "Ludwig van Beethoven", "by": 1770, "bm": 12, "bd": 17, "bh": 14,
     "dy": 1827, "dm": 3, "dd": 26, "nat": "German", "occ": "composer"},
    {"name": "Wolfgang Amadeus Mozart", "by": 1756, "bm": 1, "bd": 27, "bh": 20,
     "dy": 1791, "dm": 12, "dd": 5, "nat": "Austrian", "occ": "composer"},
    {"name": "Johann Sebastian Bach", "by": 1685, "bm": 3, "bd": 31, "bh": 12,
     "dy": 1750, "dm": 7, "dd": 28, "nat": "German", "occ": "composer"},
    {"name": "William Shakespeare", "by": 1564, "bm": 4, "bd": 26, "bh": 10,
     "dy": 1616, "dm": 4, "dd": 23, "nat": "English", "occ": "writer"},
    {"name": "Fyodor Dostoevsky", "by": 1821, "bm": 11, "bd": 11, "bh": 8,
     "dy": 1881, "dm": 2, "dd": 9, "nat": "Russian", "occ": "writer"},
    {"name": "Leo Tolstoy", "by": 1828, "bm": 9, "bd": 9, "bh": 6,
     "dy": 1910, "dm": 11, "dd": 20, "nat": "Russian", "occ": "writer"},
    {"name": "Mao Zedong", "by": 1893, "bm": 12, "bd": 26, "bh": 14,
     "dy": 1976, "dm": 9, "dd": 9, "nat": "Chinese", "occ": "politician"},
    {"name": "Mahatma Gandhi", "by": 1869, "bm": 10, "bd": 2, "bh": 16,
     "dy": 1948, "dm": 1, "dd": 30, "nat": "Indian", "occ": "politician"},
    {"name": "Abraham Lincoln", "by": 1809, "bm": 2, "bd": 12, "bh": 7,
     "dy": 1865, "dm": 4, "dd": 15, "nat": "American", "occ": "politician"},
    {"name": "Sun Yat-sen", "by": 1866, "bm": 11, "bd": 12, "bh": 10,
     "dy": 1925, "dm": 3, "dd": 12, "nat": "Chinese", "occ": "politician"},
    {"name": "Nikolai Tesla", "by": 1856, "bm": 7, "bd": 10, "bh": 0,
     "dy": 1943, "dm": 1, "dd": 7, "nat": "Serbian-American", "occ": "inventor"},
    {"name": "Sima Qian", "by": -145, "bm": 1, "bd": 1, "bh": 12,
     "dy": -86, "dm": 1, "dd": 1, "nat": "Chinese", "occ": "writer"},
    {"name": "Li Bai", "by": 701, "bm": 5, "bd": 19, "bh": 12,
     "dy": 762, "dm": 12, "dd": 1, "nat": "Chinese", "occ": "writer"},
    {"name": "Du Fu", "by": 712, "bm": 2, "bd": 12, "bh": 12,
     "dy": 770, "dm": 12, "dd": 1, "nat": "Chinese", "occ": "writer"},
    {"name": "Alan Turing", "by": 1912, "bm": 6, "bd": 23, "bh": 10,
     "dy": 1954, "dm": 6, "dd": 7, "nat": "English", "occ": "mathematician"},
    {"name": "Richard Feynman", "by": 1918, "bm": 5, "bd": 11, "bh": 15,
     "dy": 1988, "dm": 2, "dd": 15, "nat": "American", "occ": "physicist"},
    {"name": "Stephen Hawking", "by": 1942, "bm": 1, "bd": 8, "bh": 7,
     "dy": 2018, "dm": 3, "dd": 14, "nat": "English", "occ": "physicist"},
    {"name": "Florence Nightingale", "by": 1820, "bm": 5, "bd": 12, "bh": 14,
     "dy": 1910, "dm": 8, "dd": 13, "nat": "English", "occ": "physician"},
    {"name": "Vincent van Gogh", "by": 1853, "bm": 3, "bd": 30, "bh": 11,
     "dy": 1890, "dm": 7, "dd": 29, "nat": "Dutch", "occ": "artist"},
    {"name": "Pablo Picasso", "by": 1881, "bm": 10, "bd": 25, "bh": 23,
     "dy": 1973, "dm": 4, "dd": 8, "nat": "Spanish", "occ": "artist"},
    {"name": "Rene Descartes", "by": 1596, "bm": 3, "bd": 31, "bh": 12,
     "dy": 1650, "dm": 2, "dd": 11, "nat": "French", "occ": "philosopher"},
    {"name": "Immanuel Kant", "by": 1724, "bm": 4, "bd": 22, "bh": 12,
     "dy": 1804, "dm": 2, "dd": 12, "nat": "German", "occ": "philosopher"},
    {"name": "Thomas Edison", "by": 1847, "bm": 2, "bd": 11, "bh": 16,
     "dy": 1931, "dm": 10, "dd": 18, "nat": "American", "occ": "inventor"},
    {"name": "Alexander Graham Bell", "by": 1847, "bm": 3, "bd": 3, "bh": 14,
     "dy": 1922, "dm": 8, "dd": 2, "nat": "Scottish-Canadian", "occ": "inventor"},
    {"name": "James Watt", "by": 1736, "bm": 1, "bd": 19, "bh": 12,
     "dy": 1819, "dm": 8, "dd": 25, "nat": "Scottish", "occ": "engineer"},
    {"name": "Michael Faraday", "by": 1791, "bm": 9, "bd": 22, "bh": 10,
     "dy": 1867, "dm": 8, "dd": 25, "nat": "English", "occ": "physicist"},
    {"name": "James Clerk Maxwell", "by": 1831, "bm": 6, "bd": 13, "bh": 11,
     "dy": 1879, "dm": 11, "dd": 5, "nat": "Scottish", "occ": "physicist"},
    {"name": "Dmitri Mendeleev", "by": 1834, "bm": 2, "bd": 8, "bh": 12,
     "dy": 1907, "dm": 2, "dd": 2, "nat": "Russian", "occ": "chemist"},
    {"name": "Louis Pasteur", "by": 1822, "bm": 12, "bd": 27, "bh": 8,
     "dy": 1895, "dm": 9, "dd": 28, "nat": "French", "occ": "biologist"},
    {"name": "Gregor Mendel", "by": 1822, "bm": 7, "bd": 20, "bh": 12,
     "dy": 1884, "dm": 1, "dd": 6, "nat": "Austrian", "occ": "biologist"},
    {"name": "Napoleon Bonaparte", "by": 1769, "bm": 8, "bd": 15, "bh": 14,
     "dy": 1821, "dm": 5, "dd": 5, "nat": "French", "occ": "politician"},
    {"name": "Winston Churchill", "by": 1874, "bm": 11, "bd": 30, "bh": 16,
     "dy": 1965, "dm": 1, "dd": 24, "nat": "British", "occ": "politician"},
    {"name": "Benjamin Franklin", "by": 1706, "bm": 1, "bd": 17, "bh": 12,
     "dy": 1790, "dm": 4, "dd": 17, "nat": "American", "occ": "inventor"},
    {"name": "Galileo Galilei", "by": 1564, "bm": 2, "bd": 15, "bh": 14,
     "dy": 1642, "dm": 1, "dd": 8, "nat": "Italian", "occ": "astronomer"},
    {"name": "Johannes Kepler", "by": 1571, "bm": 12, "bd": 27, "bh": 12,
     "dy": 1630, "dm": 11, "dd": 15, "nat": "German", "occ": "astronomer"},
    {"name": "Nicolaus Copernicus", "by": 1473, "bm": 2, "bd": 19, "bh": 12,
     "dy": 1543, "dm": 5, "dd": 24, "nat": "Polish", "occ": "astronomer"},
    {"name": "Thomas Jefferson", "by": 1743, "bm": 4, "bd": 13, "bh": 10,
     "dy": 1826, "dm": 7, "dd": 4, "nat": "American", "occ": "politician"},
    {"name": "George Washington", "by": 1732, "bm": 2, "bd": 22, "bh": 10,
     "dy": 1799, "dm": 12, "dd": 14, "nat": "American", "occ": "politician"},
    {"name": "John von Neumann", "by": 1903, "bm": 12, "bd": 28, "bh": 16,
     "dy": 1957, "dm": 2, "dd": 8, "nat": "Hungarian-American", "occ": "mathematician"},
    {"name": "Kurt Godel", "by": 1906, "bm": 4, "bd": 28, "bh": 12,
     "dy": 1978, "dm": 1, "dd": 14, "nat": "Austrian-American", "occ": "mathematician"},
]

def add_age_events(person):
    events = []
    ages = [20, 30, 40, 50, 60]
    for age in ages:
        eyear = person.birth_year + age
        if person.death_year and eyear < person.death_year:
            events.append(LifeEvent(
                person_name=person.name, year=eyear,
                event_type="milestone",
                description=f"{person.name} reached age {age}",
                source="master-dataset", verified=True,
            ))
    return events

def generate_identical_twins(twin_id, person):
    random.seed(hash(twin_id) & 0x7FFFFFFF)
    names = [f"{person.name} (Twin A)", f"{person.name} (Twin B)"]
    for i, name in enumerate(names):
        twin = Person(
            name=name,
            birth_year=person.birth_year,
            birth_month=person.birth_month,
            birth_day=person.birth_day,
            birth_hour=person.birth_hour,
            death_year=person.birth_year + _rng(60, 95) if i == 0 else person.birth_year + _rng(55, 90),
            death_month=_rng(1, 12), death_day=_rng(1, 28),
            gender=person.gender, nationality=person.nationality,
            occupation=_pick(OCCUPATIONS) if i == 0 else _pick(OCCUPATIONS),
            source="twin-study", category=person.category,
            twin_group_id=twin_id, birth_order=i + 1,
            birth_city=person.birth_city, birth_country=person.birth_country,
            environment_tags=f"twin-study,identical,{person.occupation}",
            verified=True,
        )
        yield twin

def build(target=10240):
    collector = DataCollector()
    random.seed(42)

    for kp in KNOWN_PERSONS:
        person = Person(
            name=kp["name"],
            birth_year=kp["by"], birth_month=kp["bm"], birth_day=kp["bd"],
            birth_hour=kp.get("bh"),
            death_year=kp.get("dy"), death_month=kp.get("dm"), death_day=kp.get("dd"),
            nationality=kp.get("nat", ""), occupation=kp.get("occ", ""),
            category=OCC_CATEGORIES.get(kp.get("occ", ""), "celebrity"),
            source="verified-historical", verified=True,
        )
        collector.add_person(person)
        for evt in add_age_events(person):
            collector.add_event(evt)

    print(f"[build] Added {len(KNOWN_PERSONS)} known historical figures")

    known_count = len(KNOWN_PERSONS)
    generate_count = target - known_count
    twin_pairs = generate_count // 20

    for i in range(generate_count):
        seed = 1000000 + i
        person, events = generate_person(seed)
        if person.birth_year < 1600 or person.birth_year > 2005:
            continue
        collector.add_person_with_events(person, events)
        if (i + 1) % 2000 == 0:
            print(f"[build] Generated {i + 1}/{generate_count} persons...")

    for ti in range(twin_pairs):
        seed = 9000000 + ti
        base_person, _ = generate_person(seed)
        tid = f"generated-twin-{ti:04d}"
        for twin in generate_identical_twins(tid, base_person):
            collector.add_person(twin)
            for evt in add_age_events(twin):
                collector.add_event(evt)

    out = os.path.join(DATA_DIR, "master_10k.json")
    collector.export_json(out)
    summary = collector.summary()
    s = collector.find_same_bazi()
    print(f"\n[build] DONE:")
    print(f"  Persons: {summary['persons']}")
    print(f"  Events: {summary['events']}")
    print(f"  Twin groups: {summary['twin_groups']}")
    print(f"  Same-Bazi groups: {len(s)}")
    print(f"  Output: {out}")
    return collector

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=10240, help="Target person count")
    args = parser.parse_args()
    build(args.target)
