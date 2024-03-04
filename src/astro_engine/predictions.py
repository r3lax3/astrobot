from datetime import datetime, timedelta
from typing import List, Optional

import swisseph as swe

from src.astro_engine.models import AstroEvent, User
from src.utils import convert_from_utc, convert_to_utc, get_timezone_offset

# 10 планет для натальной карты
NATAL_PLANETS = [
    swe.SUN,
    swe.MOON,
    swe.MERCURY,
    swe.VENUS,
    swe.MARS,
    swe.JUPITER,
    swe.SATURN,
    swe.URANUS,
    swe.NEPTUNE,
    swe.PLUTO,
]
# 5 планет для транзитной карты
TRANSIT_PLANETS = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS]

ASPECTS = [0, 60, 90, 120, 180]
ORBIS = 0.1
ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]


def find_peak_time(
    time: datetime,
    natal_position: float,
    transit_planet: int,
    aspect_value: int
) -> datetime:
    julian_day_time = swe.julday(
        time.year,
        time.month,
        time.day,
        time.hour + time.minute / 60
    )

    transit_planet_data = swe.calc_ut(
        julian_day_time, transit_planet, swe.FLG_SWIEPH | swe.FLG_SPEED
    )
    transit_position = transit_planet_data[0][0]
    transit_speed = transit_planet_data[0][3]

    diff = abs(transit_position - natal_position - aspect_value) % 360
    time_to_peak = diff / abs(transit_speed)

    peak_time = time + timedelta(days=time_to_peak)
    return peak_time


def calculate_aspect(
    transit_position: float, natal_position: float, orbis: float
) -> Optional[int]:
    """
    Вычислить аспект между двумя планетами на основе их текущих позиций.

    :param transit_position: Позиция планеты в движении.
    :param natal_position: Натальная позиция планеты.
    :return: Значение аспекта (если есть) или None.
    """
    diff = (
        abs(transit_position - natal_position) % 360
    )  # Подсчет разницы в градусах между планетами
    for aspect in ASPECTS:
        if (
            abs(diff - aspect) <= orbis
        ):  # Если разница близка к одному из аспектов, возвращаем этот аспект
            return aspect
    return None  # Нет соответствующего аспекта


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

            aspect_value = calculate_aspect(
                transit_planet_position, natal_planet_position, orbis=ORBIS
            )

            if aspect_value:  # Если аспект существует, добавляем событие в список
                events.append(
                    AstroEvent(
                        natal_planet=natal_planet,
                        transit_planet=transit_planet,
                        aspect=aspect_value,
                        peak_at=time if transit_planet == swe.MOON else None,
                    )
                )

    return events


def get_astro_events_from_period(
    start: datetime,
    finish: datetime,
    user: User
) -> List[AstroEvent]:
    timezone = int(
        get_timezone_offset(
            latitude=user.current_location.latitude,
            longitude=user.current_location.longitude,
        )
    )

    # Преобразуем время в UTC
    start_utc = convert_to_utc(start, timezone)

    step = timedelta(minutes=10)
    current_time = start_utc

    all_events = []

    while current_time <= finish:
        events_at_current_time = get_astro_event_at_time(current_time, user)
        all_events.extend(events_at_current_time)
        current_time += step

    # Преобразовываем время событий из UTC обратно в локальное
    all_events_converted = [
        AstroEvent(
            natal_planet=event.natal_planet,
            transit_planet=event.transit_planet,
            aspect=event.aspect,
            peak_at=convert_from_utc(event.peak_at, timezone)
            if event.peak_at
            else None,
        )
        for event in all_events
    ]

    # Удаление дубликатов на основе натальной планеты, транзитной планеты и аспекта
    unique_events_dict = {
        (event.natal_planet, event.transit_planet, event.aspect): event
        for event in all_events_converted
    }

    # Преобразование словаря обратно в список
    unique_events = list(unique_events_dict.values())

    unique_sorted_events = sort_astro_events(unique_events)
    return unique_sorted_events


def sort_astro_events(events):

    events_with_peak = remove_duplicates(
        [event for event in events if event.peak_at is None]
    )
    events_without_peak = remove_duplicates(
        [event for event in events if event.peak_at is not None]
    )

    sorted_events_with_peak = sorted(events_with_peak, key=lambda x: x.peak_at)

    return events_without_peak + sorted_events_with_peak


def remove_duplicates(events: List[AstroEvent]) -> List[AstroEvent]:
    unique_events_list = []
    for event in events:
        # Конвертируем datetime в timestamp для хеширования, если peak_at не None
        event_key = (
            event.natal_planet,
            event.transit_planet,
            event.aspect
        )
        if event_key not in unique_events_list:
            unique_events_list.append(event)

    return unique_events_list
