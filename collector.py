import json
import os
import re
import csv
import math
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def shichen_from_hour(hour):
    if hour is None:
        return "", -1
    return DIZHI[((hour + 1) // 2) % 12], ((hour + 1) // 2) % 12

WU_SHOU_DUN = {
    0: 0, 1: 2, 2: 4, 3: 6, 4: 8,
    5: 0, 6: 2, 7: 4, 8: 6, 9: 8,
}

def calc_bazi(year, month, day, hour):
    year_gan_idx = (year - 4) % 10
    year_zhi_idx = (year - 4) % 12
    gan = TIANGAN[year_gan_idx]
    zhi = DIZHI[year_zhi_idx]
    month_zhi_idx = (year_zhi_idx % 3 * 4 + month + 1) % 12
    month_gan_idx = (year_gan_idx % 5 * 2 + (month + 1)) % 10
    month_gan = TIANGAN[month_gan_idx]
    month_zhi = DIZHI[month_zhi_idx]
    day_offset = (year - 1) * 365 + (year - 1) // 4 - (year - 1) // 100 + (year - 1) // 400
    month_days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        month_days[2] = 29
    for m in range(1, month):
        day_offset += month_days[m]
    day_offset += day
    day_gan_idx = day_offset % 10
    day_zhi_idx = day_offset % 12
    day_gan = TIANGAN[day_gan_idx]
    day_zhi = DIZHI[day_zhi_idx]
    hour_zhi_str, hour_zhi_idx = shichen_from_hour(hour)
    hour_gan_start = WU_SHOU_DUN.get(day_gan_idx % 10, 0)
    hour_gan_idx = (hour_gan_start + hour_zhi_idx * 2) % 10 if hour_zhi_idx >= 0 else 0
    hour_gan = TIANGAN[hour_gan_idx]
    return f"{gan}{zhi} {month_gan}{month_zhi} {day_gan}{day_zhi} {hour_gan}{hour_zhi_str}"

@dataclass
class Relation:
    person_name: str
    relation_type: str  # twin, sibling, spouse, parent, child
    twin_group_id: Optional[str] = None
    birth_order: int = 1  # 1=first, 2=second etc

@dataclass
class Person:
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: Optional[int] = None
    birth_minute: Optional[int] = None
    death_year: Optional[int] = None
    death_month: Optional[int] = None
    death_day: Optional[int] = None
    gender: str = ""
    nationality: str = ""
    occupation: str = ""
    category: str = "celebrity"
    source: str = ""
    bazi: str = ""
    shichen: str = ""
    wiki_url: str = ""
    verified: bool = False
    twin_group_id: Optional[str] = None
    birth_order: int = 1
    birth_city: str = ""
    birth_country: str = ""
    family_rank: int = 0
    family_wealth: str = ""
    relations: list = field(default_factory=list)
    environment_tags: str = ""
    confidence: float = 1.0
    disputed: bool = False
    corrected: bool = False
    correction_note: str = ""
    quality_tags: list = field(default_factory=list)
    training_batch_id: int = 0
    used_for_training: bool = False
    death_cause: str = ""
    birth_accuracy: str = "exact"
    duplicate_of: str = ""
    source_priority: int = 0

    def __post_init__(self):
        if not self.bazi and self.birth_hour is not None:
            try:
                self.bazi = calc_bazi(self.birth_year, self.birth_month, self.birth_day, self.birth_hour)
            except Exception:
                pass
        if not self.shichen and self.birth_hour is not None:
            self.shichen, _ = shichen_from_hour(self.birth_hour)

@dataclass
class LifeEvent:
    person_name: str
    year: int
    month: int = 1
    day: int = 1
    event_type: str = ""
    description: str = ""
    source: str = ""
    verified: bool = False
    event_impact: float = 0.0

class DataCollector:
    def __init__(self):
        self.persons: dict[str, Person] = {}
        self.events: list[LifeEvent] = []
        self.twin_groups: dict[str, list[str]] = {}

    def add_person(self, person: Person):
        key = person.name
        if not person.bazi and person.birth_hour is not None:
            try:
                person.bazi = calc_bazi(person.birth_year, person.birth_month, person.birth_day, person.birth_hour)
            except Exception:
                pass
        if person.twin_group_id:
            if person.twin_group_id not in self.twin_groups:
                self.twin_groups[person.twin_group_id] = []
            if person.name not in self.twin_groups[person.twin_group_id]:
                self.twin_groups[person.twin_group_id].append(person.name)
        self.persons[key] = person

    def add_event(self, event: LifeEvent):
        self.events.append(event)

    def add_person_with_events(self, person: Person, events: list[LifeEvent]):
        self.add_person(person)
        for evt in events:
            evt.person_name = person.name
            self.add_event(evt)

    def add_relation(self, name_a: str, name_b: str, rtype: str, twin_group_id: Optional[str] = None, order_a: int = 1, order_b: int = 2):
        for n in (name_a, name_b):
            if n in self.persons:
                p = self.persons[n]
                if not hasattr(p, 'relations') or p.relations is None:
                    p.relations = []
                p.relations.append({"related_to": name_b if n == name_a else name_a,
                                    "relation_type": rtype,
                                    "twin_group_id": twin_group_id,
                                    "birth_order": order_a if n == name_a else order_b})

    def load_wikipedia_json(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)
        for rec in records:
            p = Person(
                name=rec.get("name", ""),
                birth_year=int(rec.get("birth_year", 0)),
                birth_month=int(rec.get("birth_month", 1)),
                birth_day=int(rec.get("birth_day", 1)),
                birth_hour=int(rec["birth_hour"]) if rec.get("birth_hour") is not None else None,
                death_year=int(rec["death_year"]) if rec.get("death_year") else None,
                death_month=int(rec["death_month"]) if rec.get("death_month") else None,
                death_day=int(rec["death_day"]) if rec.get("death_day") else None,
                nationality=rec.get("nationality", ""),
                occupation=rec.get("occupation", ""),
                source=rec.get("source", "wikipedia"),
                wiki_url=rec.get("wiki_url", ""),
                verified=True,
            )
            self.add_person(p)

    def export_json(self, filepath: str = ""):
        if not filepath:
            filepath = os.path.join(DATA_DIR, "persons_collected.json")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        persons_list = []
        seen_names = set()
        for p in self.persons.values():
            if p.name not in seen_names:
                persons_list.append(asdict(p))
                seen_names.add(p.name)
            else:
                pass
        data = {
            "persons": persons_list,
            "events": [asdict(e) for e in self.events],
            "twin_groups": {k: v for k, v in self.twin_groups.items()},
            "summary": {
                "total_persons": len(persons_list),
                "total_events": len(self.events),
                "total_twin_groups": len(self.twin_groups),
                "twin_persons": sum(len(v) for v in self.twin_groups.values()),
                "sources": self._count_sources(persons_list),
                "exported_at": str(datetime.now()),
            }
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[collector] Exported {len(persons_list)} persons, {len(self.events)} events, "
              f"{len(self.twin_groups)} twin groups -> {filepath}")
        return filepath

    def _count_sources(self, persons_list=None):
        if persons_list is None:
            persons_list = list(self.persons.values())
        counts = {}
        for p in persons_list:
            src = p.get("source", "unknown") if isinstance(p, dict) else (p.source or "unknown")
            counts[src] = counts.get(src, 0) + 1
        return counts

    def summary(self):
        return {
            "persons": len(self.persons),
            "events": len(self.events),
            "twin_groups": len(self.twin_groups),
            "by_source": self._count_sources(),
        }

    def find_same_bazi(self):
        groups = {}
        for p in self.persons.values():
            if p.bazi:
                groups.setdefault(p.bazi, []).append(p.name)
        return {b: names for b, names in groups.items() if len(names) > 1}

    def twin_summary(self):
        tw = self.find_same_bazi()
        return {
            "total_same_bazi_groups": len(tw),
            "same_bazi_persons": sum(len(v) for v in tw.values()),
            "twin_groups": self.twin_groups,
        }

if __name__ == "__main__":
    c = DataCollector()
    p1 = Person(name="Albert Einstein", birth_year=1879, birth_month=3, birth_day=14,
                birth_hour=11, death_year=1955, nationality="German", occupation="scientist",
                source="wikipedia", verified=True)
    c.add_person(p1)
    c.add_event(LifeEvent(person_name="Albert Einstein", year=1905, event_type="achievement",
                          description="Published Annus Mirabilis papers", verified=True))
    c.add_event(LifeEvent(person_name="Albert Einstein", year=1921, event_type="award",
                          description="Nobel Prize in Physics", verified=True))
    c.export_json()
    print(c.summary())
