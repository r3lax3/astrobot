from datetime import datetime, timedelta
from typing import List, Optional, Dict

import swisseph as swe

from src.astro_engine.models import AstroEvent, User
from src.enums import SwissEphPlanet
from .utils import get_juliday, sort_astro_events


NATAL_PLANETS = [
    SwissEphPlanet.SUN,
    SwissEphPlanet.MOON,
    SwissEphPlanet.MERCURY,
    SwissEphPlanet.VENUS,
    SwissEphPlanet.MARS,
    SwissEphPlanet.JUPITER,
    SwissEphPlanet.SATURN,
    SwissEphPlanet.URANUS,
    SwissEphPlanet.NEPTUNE,
    SwissEphPlanet.PLUTO,
]
TRANSIT_PLANETS = [
    SwissEphPlanet.SUN,
    SwissEphPlanet.MOON,
    SwissEphPlanet.MERCURY,
    SwissEphPlanet.VENUS,
    SwissEphPlanet.MARS
]

ASPECTS = [0, 30, 60, 90, 120, 180, 240, 270, 300, 330, 360]
ORBIS = 0.1
ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]


def find_peak_time(
    time: datetime,
    first_planet_position: float,
    second_planet: int,
    aspect_value: int
) -> datetime:
    julian_day_time = get_juliday(time)

    transit_planet_data = swe.calc_ut(
        julian_day_time,
        second_planet,
        swe.FLG_SWIEPH | swe.FLG_SPEED
    )
    transit_position = transit_planet_data[0][0]
    transit_speed = transit_planet_data[0][3]

    diff = abs(transit_position - first_planet_position - aspect_value) % 360
    time_to_peak = diff / abs(transit_speed)

    peak_time = time + timedelta(days=time_to_peak)
    return peak_time


def calculate_aspect(
    transit_position: float,
    natal_position: float,
) -> Optional[int]:
    """
    Вычислить аспект между двумя планетами на основе их текущих позиций.
    """
    diff = abs(transit_position - natal_position)
    for aspect in ASPECTS:
        diff_with_aspect = abs(diff - aspect)
        if diff_with_aspect < ORBIS:
            if aspect > 180:
                return 360 - aspect
            return aspect


def get_astro_event_at_time(time: datetime, user: User) -> List[AstroEvent]:
    """
    Получить все астрологические события для заданного времени.
    """
    events = []

    # Преобразование текущего времени в юлианскую дату
    julian_day_time = swe.julday(
        time.year,
        time.month,
        time.day,
        time.hour + time.minute / 60
    )

    # Преобразование времени рождения пользователя в юлианскую дату
    julian_day_birth = swe.julday(
        user.birth_datetime.year,
        user.birth_datetime.month,
        user.birth_datetime.day,
        user.birth_datetime.hour + user.birth_datetime.minute / 60,
    )

    # Вычисление натальных позиций для всех планет на основе даты рождения пользователя
    natal_positions = {
        planet: swe.calc_ut(julian_day_birth, planet, swe.FLG_SWIEPH)[0][0]
        for planet in NATAL_PLANETS
    }

    for transit_planet in TRANSIT_PLANETS:
        # Получение текущей позиции планеты в движении
        transit_planet_position = swe.calc_ut(
            julian_day_time, transit_planet, swe.FLG_SWIEPH
        )[0][0]

        for natal_planet, natal_planet_position in natal_positions.items():
            # Вычисление аспекта между
            # текущей позицией планеты и натальной позицией

            aspect = calculate_aspect(
                transit_planet_position,
                natal_planet_position
            )

            if aspect is not None:  # Если аспект существует, добавляем событие в список
                events.append(
                    AstroEvent(
                        natal_planet=natal_planet,
                        transit_planet=transit_planet,
                        aspect=aspect,
                        peak_at=time
                    )
                )

    return events


def get_astro_events_from_period(
    start: datetime,
    finish: datetime,
    user: User
) -> List[AstroEvent]:
    step = timedelta(minutes=10)
    current_time = start

    all_events = []
    while current_time <= finish:
        events_at_current_time = get_astro_event_at_time(current_time, user)
        all_events.extend(events_at_current_time)
        current_time += step

    # Удаление дубликатов на основе натальной планеты, транзитной планеты и аспекта
    unique_events_dict = {
        (
            event.natal_planet,
            event.transit_planet,
            event.aspect
        ): event
        for event in all_events
    }

    # Преобразование словаря обратно в список
    unique_events = list(unique_events_dict.values())

    unique_sorted_events = sort_astro_events(unique_events)
    return unique_sorted_events


def get_astro_events_from_period_with_duplicates(
    start: datetime,
    finish: datetime,
    user: User
) -> List[AstroEvent]:
    step = timedelta(minutes=10)
    current_time = start
    all_events = []

    while current_time <= finish:
        events_at_current_time = get_astro_event_at_time(current_time, user)
        all_events.extend(events_at_current_time)
        current_time += step

    unique_events_dict: Dict[(int, int, int), List[List[AstroEvent]]] = {}
    for event in all_events:
        key = (event.natal_planet, event.transit_planet, event.aspect)
        if key not in unique_events_dict:
            unique_events_dict[key] = [[event]]
        else:
            last_group = unique_events_dict[key][-1]
            if (event.peak_at - last_group[-1].peak_at) > timedelta(hours=2):
                unique_events_dict[key].append([event])
            else:
                last_group.append(event)

    unique_events = []
    for events_groups_list in unique_events_dict.values():
        for events_group in events_groups_list:
            avg_peak_time = sum(
                (event.peak_at.timestamp() for event in events_group)
            ) / len(events_group)

            avg_event = events_group[0]
            avg_event.peak_at = datetime.fromtimestamp(avg_peak_time)

            unique_events.append(avg_event)

    return unique_events
