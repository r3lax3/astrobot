from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

from astropy.time import Time
from astropy.coordinates import get_body, solar_system_ephemeris
import pytz
from timezonefinder import TimezoneFinder  # Добавлен импорт


solar_system_ephemeris.set("de440")


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
    natal_planet: str
    transit_planet: str
    aspect: int
    peak_at: datetime | None


NATAL_PLANETS = [
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "ceres", "eris"
]
TRANSIT_PLANETS = ["sun", "moon", "mercury", "venus", "mars"]
ASPECTS = [0, 60, 90, 120, 180]
ORBIS = 0.1


def get_timezone_offset(latitude, longitude):
    obj = TimezoneFinder()
    tz_name = obj.timezone_at(lat=latitude, lng=longitude)
    if tz_name:
        timezone = pytz.timezone(tz_name)
        offset = timezone.utcoffset(datetime.utcnow())
        if offset:  # Проверка на None
            return offset.total_seconds() / 3600
    return None


def convert_to_utc(dt: datetime, offset: int) -> datetime:
    return dt - timedelta(hours=offset)


def convert_from_utc(dt: datetime, offset: int) -> datetime:
    return dt + timedelta(hours=offset)


def calculate_aspect(transit_position: float, natal_position: float, orbis: float) -> Optional[int]:
    diff = abs(transit_position - natal_position) % 360
    for aspect in ASPECTS:
        if abs(diff - aspect) <= orbis:
            return aspect
    return None


def get_astro_event_at_time(time: datetime, user: User) -> List[AstroEvent]:
    events = []
    time_utc = Time(time)

    natal_positions = {
        planet: get_body(planet, time_utc).ra.degree
        for planet in NATAL_PLANETS
    }

    for transit_planet in TRANSIT_PLANETS:
        transit_planet_position = get_body(transit_planet, time_utc).ra.degree

        for natal_planet, natal_planet_position in natal_positions.items():
            aspect_value = calculate_aspect(transit_planet_position, natal_planet_position, orbis=ORBIS)

            if aspect_value:
                events.append(
                    AstroEvent(
                        natal_planet=natal_planet,
                        transit_planet=transit_planet,
                        aspect=aspect_value,
                        peak_at=time if transit_planet == "moon" else None
                    )
                )

    return events


def get_astro_events_from_period(start: datetime, finish: datetime, user: User) -> List[AstroEvent]:
    timezone_offset = get_timezone_offset(user.current_location.latitude, user.current_location.longitude)
    
    start_utc = convert_to_utc(start, timezone_offset)
    finish_utc = convert_to_utc(finish, timezone_offset)

    step = timedelta(minutes=10)
    current_time = start_utc

    all_events = []

    while current_time <= finish_utc:
        events_at_current_time = get_astro_event_at_time(current_time, user)
        all_events.extend(events_at_current_time)
        current_time += step

    all_events_converted = [
        AstroEvent(
            natal_planet=event.natal_planet,
            transit_planet=event.transit_planet,
            aspect=event.aspect,
            peak_at=convert_from_utc(event.peak_at, timezone_offset) if event.peak_at else None
        )
        for event in all_events
    ]

    unique_events_dict = {
        (event.natal_planet, event.transit_planet, event.aspect): event
        for event in all_events_converted
    }

    unique_events = list(unique_events_dict.values())

    return unique_events


if __name__ == '__main__':
    # Импортируем необходимые библиотеки

    # Тестовые данные для пользователя
    test_user = User(
        birth_datetime=datetime(1990, 1, 1, 12, 0),
        birth_location=Location(55.7558, 37.6176),
        current_location=Location(40.7128, -74.0060)
    )

    # Тестовый временной интервал
    start_time = datetime(2023, 8, 20, 0, 0)
    end_time = datetime(2023, 8, 21, 0, 0)

    events = get_astro_events_from_period(start_time, end_time, test_user)
    for event in events:
        print(event)

# if __name__ == '__main__':
#     # Тестовые данные
#     user_birth_datetime = datetime(2005, 10, 19, 9, 32)  # Дата и время рождения: 15 июня 1995 года в 12:00
#     user_birth_location = Location(32.08452998284642, 49.42092491956057)  # Место рождения: Черкассы, Украина
#     user_current_location = Location(30.772546984752733, 50.12033469399557)  # Текущее местоположение: Киев, Украина
#
#     test_user = User(
#         birth_datetime=user_birth_datetime,
#         birth_location=user_birth_location,
#         current_location=user_current_location
#     )
#
#     start_date = datetime(2023, 8, 3, 3)
#     end_date = datetime(2023, 8, 4, 3)
#
#     # Получение астрологических событий и вывод результатов
#
#     time_list = []
#     for x in range(100):
#         print(x+1)
#         start = time.time()
#
#         astro_events = get_astro_events_from_period(start_date, end_date, test_user)
#
#         time_list.append(time.time() - start)
#     print(f'В среднем - {sum(time_list) / len(time_list)}')

    #
    # start = time.time()
    #
    # astro_events = get_astro_events_from_period(start_date, end_date, test_user)
    #
    # delta = time.time() - start
    # print(f'Заняло времени - {delta} секунд\n')
    #
    # for astro_event in astro_events:
    #
    #     peak = ""
    #     if astro_event.peak_at:
    #         peak = f"Peak at: {astro_event.peak_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    #
    #     print(
    #         f"Natal: {swe.get_planet_name(astro_event.natal_planet)}\n"
    #         f"Transit: {swe.get_planet_name(astro_event.transit_planet)}\n"
    #         f"Aspect: {astro_event.aspect}\n" + peak
    #     )
