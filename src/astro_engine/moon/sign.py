import logging

from datetime import datetime, timedelta
from typing import Literal, Union, Dict

from src import config
from src.enums import MoonPhase, SwissEphPlanet, ZodiacSign

from ..models import Location, User, TimePeriod
from ..utils import get_juliday, calculate_planet_degrees_ut

# Константы
SECONDS_IN_DAY = 24 * 60 * 60
ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
ZODIAC_SIGNS = [
    ZodiacSign.ARIES,
    ZodiacSign.TAURUS,
    ZodiacSign.GEMINI,
    ZodiacSign.CANCER,
    ZodiacSign.LEO,
    ZodiacSign.VIRGO,
    ZodiacSign.LIBRA,
    ZodiacSign.SCORPIO,
    ZodiacSign.SAGITTARIUS,
    ZodiacSign.CAPRICORN,
    ZodiacSign.AQUARIUS,
    ZodiacSign.PISCES,
]

MOON_PHASES_RANGES = {
    (0, 0.01): MoonPhase.NEW_MOON,
    (0.05, 0.45): (MoonPhase.WAXING_CRESCENT, MoonPhase.WANING_CRESCENT),
    (0.45, 0.55): (MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER),
    (0.55, 0.99): (MoonPhase.WAXING_GIBBOUS, MoonPhase.WANING_GIBBOUS),
    (0.99, 1): MoonPhase.FULL_MOON,
}
ISO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT: str = config.get("database.time_format")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

LOGGER = logging.getLogger(__name__)


def get_moon_signs_at_date(
    date: datetime,
    timezone_offset: int,
    location: Location
) -> Dict[str, Union[ZodiacSign, str]]:
    """
    Определяет зодиакальный знак Луны на начало и конец заданной даты.
    """
    date = datetime(date.year, date.month, date.day)
    start_of_day = date - timedelta(hours=timezone_offset)
    end_of_day = start_of_day + timedelta(hours=23, minutes=58)

    start_sign = _get_moon_sign(start_of_day, location)
    end_sign = _get_moon_sign(end_of_day, location)

    result = {"start_sign": start_sign}

    if start_sign != end_sign:
        left_time, right_time = start_of_day, end_of_day
        while right_time - left_time > timedelta(minutes=1):
            middle_time = left_time + (right_time - left_time) / 2
            if _get_moon_sign(middle_time, location) == start_sign:
                left_time = middle_time
            else:
                right_time = middle_time
        change_time = left_time
        result.update(
            {
                "change_time": (
                    change_time + timedelta(hours=timezone_offset)
                ).strftime(TIME_FORMAT),
                "end_sign": end_sign,
            }
        )

    return result


def get_moon_sign_period(utcdate: datetime, user: User) -> TimePeriod:
    start = _find_moon_sign_start(utcdate, user)
    end = _find_moon_sign_end(utcdate, user)

    return TimePeriod(start=start, end=end)


def _get_moon_sign(date: datetime, location: Location) -> ZodiacSign:
    """
    Вычисляет знак луны для переданой точки времени и координат
    """
    juliday = get_juliday(date)
    moon_degree = calculate_planet_degrees_ut(
        juliday,
        SwissEphPlanet.MOON,
        location
    )
    return _calculate_moon_sign(moon_degree)


def _calculate_moon_sign(moon_degrees: float) -> ZodiacSign:
    for i, bound in enumerate(ZODIAC_BOUNDS):
        if moon_degrees < bound:
            return ZODIAC_SIGNS[i]
    else:
        return ZODIAC_SIGNS[-1]


def _find_moon_sign_start(utcdate: datetime, user: User) -> datetime:
    current_sign = _get_moon_sign(utcdate, user.current_location)

    search_time = utcdate
    previous_sign = current_sign

    # Идем назад по времени до смены знака
    while previous_sign == current_sign:
        search_time -= timedelta(hours=1)
        previous_sign = _get_moon_sign(search_time, user.current_location)

    return _binary_search_for_sign_change(
        search_time,
        search_time + timedelta(hours=1),
        previous_sign,
        user,
        seeking='start'
    )


def _find_moon_sign_end(utcdate: datetime, user: User) -> datetime:
    current_sign = _get_moon_sign(utcdate, user.current_location)

    search_time = utcdate
    next_sign = current_sign

    # Идем вперед по времени до смены знака
    while next_sign == current_sign:
        search_time += timedelta(hours=1)
        next_sign = _get_moon_sign(search_time, user.current_location)

    # Точное определение конца знака с помощью бинарного поиска
    return _binary_search_for_sign_change(
        utcdate,
        search_time,
        current_sign,
        user,
        seeking='end'
    )


def _binary_search_for_sign_change(
    start_time: datetime,
    end_time: datetime,
    current_sign: str,
    user: User,
    seeking: Literal['start', 'end']
) -> datetime:
    while end_time - start_time > timedelta(minutes=1):
        middle_time = start_time + (end_time - start_time) // 2
        middle_sign = _get_moon_sign(middle_time, user.current_location)

        if seeking == 'start':
            if middle_sign == current_sign:
                # Если средняя точка все еще в текущем знаке, сдвигаем начало интервала вперед
                start_time = middle_time
            else:
                # Если средняя точка уже в другом знаке, сдвигаем конец интервала назад
                end_time = middle_time

        if seeking == 'end':
            if middle_sign == current_sign:
                # Если средняя точка все еще в текущем знаке, сдвигаем начало интервала вперед
                start_time = middle_time
            else:
                # Если средняя точка уже в другом знаке, сдвигаем конец интервала назад
                end_time = middle_time

    return start_time if seeking == 'start' else end_time
