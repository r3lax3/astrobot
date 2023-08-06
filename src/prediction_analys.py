import swisseph as swe
import pytz

from typing import List, Optional
from dataclasses import dataclass

from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta


# Мутки с таймзоной

def get_timezone_offset(latitude, longitude):
    obj = TimezoneFinder()
    tz_name = obj.timezone_at(lat=latitude, lng=longitude)  # Получаем имя временной зоны
    if tz_name:
        timezone = pytz.timezone(tz_name)
        offset = timezone.utcoffset(datetime.utcnow())
        return offset.total_seconds() / 3600  # Преобразуем в часы
    return None


def convert_to_utc(dt: datetime, offset: int) -> datetime:
    return dt - timedelta(hours=offset)


def convert_from_utc(dt: datetime, offset: int) -> datetime:
    return dt + timedelta(hours=offset)


@dataclass
class Location:
    longitude: float
    latitude: float


@dataclass
class User:
    birth_datetime: datetime
    birth_location: Location
    current_location: Location


# Модель для представления астрологического события
@dataclass
class AstroEvent:
    natal_planet: int  # Planet ID
    transit_planet: int  # Planet ID
    aspect: int
    peak_at: datetime | None


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
    swe.PLUTO
]
# 5 планет для транзитной карты
TRANSIT_PLANETS = [
    swe.SUN,
    swe.MOON,
    swe.MERCURY,
    swe.VENUS,
    swe.MARS
]

ASPECTS = [0, 60, 90, 120, 180]
ORBIS = 0.1


def find_peak_time(time: datetime, natal_position: float, transit_planet: int, aspect_value: int) -> datetime:
    julian_day_time = swe.julday(
        time.year,
        time.month,
        time.day,
        time.hour + time.minute / 60
    )

    transit_planet_data = swe.calc_ut(julian_day_time, transit_planet, swe.FLG_SWIEPH | swe.FLG_SPEED)
    transit_position = transit_planet_data[0][0]
    transit_speed = transit_planet_data[0][3]

    diff = abs(transit_position - natal_position - aspect_value) % 360
    time_to_peak = diff / abs(transit_speed)

    peak_time = time + timedelta(days=time_to_peak)
    return peak_time



# Движок
def calculate_aspect(transit_position: float, natal_position: float, orbis: float) -> Optional[int]:
    """
    Вычислить аспект между двумя планетами на основе их текущих позиций.

    :param transit_position: Позиция планеты в движении.
    :param natal_position: Натальная позиция планеты.
    :return: Значение аспекта (если есть) или None.
    """
    diff = abs(transit_position - natal_position) % 360  # Подсчет разницы в градусах между планетами
    for aspect in ASPECTS:
        if abs(diff - aspect) <= orbis:  # Если разница близка к одному из аспектов, возвращаем этот аспект
            return aspect
    return None  # Нет соответствующего аспекта


def get_astro_event_at_time(time: datetime, user: User) -> List[AstroEvent]:
    """
    Получить все астрологические события для заданного времени.

    :param time: Текущее время в формате UTC.
    :param user: Информация о пользователе, включая место рождения и текущее местоположение.
    :return: Список астрологических событий для данного времени.
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
        user.birth_datetime.hour + user.birth_datetime.minute / 60
    )

    # Вычисление натальных позиций для всех планет на основе даты рождения пользователя
    natal_positions = {
        planet: swe.calc_ut(julian_day_birth, planet, swe.FLG_SWIEPH)[0][0]
        for planet in NATAL_PLANETS
    }

    for transit_planet in TRANSIT_PLANETS:
        # Получение текущей позиции планеты в движении
        transit_planet_position = swe.calc_ut(julian_day_time, transit_planet, swe.FLG_SWIEPH)[0][0]

        for natal_planet, natal_planet_position in natal_positions.items():
            # Вычисление аспекта между текущей позицией планеты и натальной позицией

            aspect_value = calculate_aspect(transit_planet_position, natal_planet_position, orbis=ORBIS)

            if aspect_value:  # Если аспект существует, добавляем событие в список
                events.append(
                    AstroEvent(
                        natal_planet=natal_planet,
                        transit_planet=transit_planet,
                        aspect=aspect_value,
                        peak_at=time if transit_planet == swe.MOON else None
                    )
                )

    return events


def get_astro_events_from_period(start: datetime, finish: datetime, user: User) -> List[AstroEvent]:
    timezone = int(
        get_timezone_offset(
            latitude=user.current_location.latitude,
            longitude=user.current_location.longitude
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
            peak_at=convert_from_utc(event.peak_at, timezone) if event.peak_at else None
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

    return unique_events


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
