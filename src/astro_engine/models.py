from dataclasses import dataclass
from datetime import datetime


@dataclass
class Location:
    longitude: float
    latitude: float


@dataclass
class User:
    birth_datetime: datetime
    birth_location: Location
    current_location: Location


@dataclass
class AstroEvent:
    natal_planet: int
    transit_planet: int
    aspect: int
    peak_at: datetime | None


@dataclass
class LunarDay:
    number: int
    start: datetime
    end: datetime


@dataclass
class TimePeriod:
    start: datetime
    end: datetime
