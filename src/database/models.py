from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    role: str
    birth_datetime: str
    birth_location_id: int
    current_location_id: int
    every_day_prediction_time: str


@dataclass
class Location:
    id: int
    type: str
    longitude: float
    latitude: float


@dataclass
class Interpretation:
    natal_planet: str
    transit_planet: str
    aspect: str
    interpretation: str


# @dataclass
# class MandatorySubChannel:
#     channel_id: int
#     title: str
#     invite_link: str
