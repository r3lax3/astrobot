import csv
import logging

import swisseph as swe

from typing import Optional, List
from datetime import datetime, timedelta

from src.enums import SwissEphPlanet

from .models import Location, AstroEvent, MonoAstroEvent


# Константы
SECONDS_IN_DAY = 24 * 60 * 60
ASPECTS = [0, 60, 90, 120, 180]

ISO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M"

LOGGER = logging.getLogger(__name__)


def calculate_planet_degrees_ut(
    juliday: float,
    planet: SwissEphPlanet,
    location: Optional[Location] = None
):
    return get_planet_data(juliday, planet, location)[0][0]


def get_planet_data(
    juliday: float,
    planet: SwissEphPlanet,
    location: Optional[Location] = None
):
    if location:
        swe.set_topo(location.longitude, location.latitude, 0)

    flag = swe.FLG_SWIEPH + swe.FLG_SPEED + swe.FLG_TOPOCTR
    return swe.calc(juliday, planet, flag)


def get_juliday(utcdate: datetime) -> float:
    """Calculates julian day from the utc time."""
    utctime = utcdate.hour + utcdate.minute / 60  # time in seconds
    julian_day = float(
        swe.julday(utcdate.year, utcdate.month, utcdate.day, utctime)
    )
    return julian_day


def calculate_aspect(
    first_planet_position: float,
    second_planet_position: float,
    orbis: float
) -> Optional[int]:
    """
    Вычислить аспект между двумя планетами на основе их текущих позиций.
    """
    diff = abs(first_planet_position - second_planet_position) % 360

    for aspect in ASPECTS:
        if abs(diff - aspect) <= orbis:
            return aspect

    return None


def find_peak_time(
    time: datetime,
    first_planet: SwissEphPlanet,
    second_planet: SwissEphPlanet,
    aspect_value: int
) -> datetime:
    julian_day_time = get_juliday(time)

    first_planet_data = get_planet_data(julian_day_time, first_planet)
    second_planet_data = get_planet_data(julian_day_time, second_planet)

    first_planet_position = first_planet_data[0][0]
    first_planet_speed = first_planet_data[0][3]

    second_planet_position = second_planet_data[0][0]
    second_planet_speed = second_planet_data[0][3]

    general_speed = abs(first_planet_speed - second_planet_speed)

    degree_diff = abs(second_planet_position - first_planet_position - aspect_value) % 360
    time_to_peak = degree_diff / general_speed

    peak_time = time + timedelta(days=time_to_peak)
    return peak_time


def sort_astro_events(events: List[AstroEvent | MonoAstroEvent]):
    events_with_peak = remove_duplicates(
        [event for event in events if event.peak_at is not None]
    )
    events_without_peak = remove_duplicates(
        [event for event in events if event.peak_at is None]
    )

    sorted_events_with_peak = sorted(events_with_peak, key=lambda x: x.peak_at)

    return events_without_peak + sorted_events_with_peak


def remove_duplicates(
    events: List[AstroEvent]
) -> List[AstroEvent]:
    unique_events_list = []
    for event in events:
        event_key = (
            event.natal_planet,
            event.transit_planet,
            event.aspect
        )
        if event_key not in unique_events_list:
            unique_events_list.append(event)

    return unique_events_list


def get_moon_in_signs_interpretations(
    file_path: str = "./moon_signs_interpretations.csv",
) -> dict[str, dict[str, str]]:
    moon_in_signs_interpretations = {}

    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sign = row["sign"]
            moon_in_signs_interpretations[sign] = {
                "general": row["general"],
                "favorable": row["favorable"],
                "unfavorable": row["unfavorable"],
            }

    return moon_in_signs_interpretations
