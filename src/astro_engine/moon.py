import ephem
import logging

from datetime import datetime
from typing import Optional
from datetime import datetime, timedelta

from src import config
from src.enums import MoonPhase

ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
ZODIAC_SIGNS = [
    "Aries", 
    "Taurus",
    "Gemini", 
    "Cancer", 
    "Leo", 
    "Virgo",
    "Libra", 
    "Scorpio", 
    "Sagittarius", 
    "Capricorn", 
    "Aquarius", 
    "Pisces"
]
MOON_PHASES_RANGES = {
    (0, 0.05): (MoonPhase.NEW_MOON),
    (0.05, 0.45): (MoonPhase.WAXING_CRESCENT, MoonPhase.WANING_CRESCENT),
    (0.45, 0.55): (MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER),
    (0.55, 0.95): (MoonPhase.WAXING_GIBBOUS, MoonPhase.WAXING_GIBBOUS),
    (0.95, 1): (MoonPhase.FULL_MOON),
}
LUNAR_MONTH = 29.53  # average length of a lunar month in days
LUNAR_DAY_LENGTH = LUNAR_MONTH / 30  # length of a lunar day in solar days
SECONDS_IN_DAY = 24 * 60 * 60
TIME_FORMAT: str = config.get('database.time_format')


def get_lunar_day(date: datetime) -> int:
    """
    Calculate the lunar day for a given date.

    Args:
    date (datetime): The date for which to calculate the lunar day.

    Returns:
    int: The lunar day.
    """
    previous_new_moon = ephem.previous_new_moon(date).datetime()
    next_new_moon = ephem.next_new_moon(date).datetime()

    # Duration of the current lunar month
    lunar_month_duration: timedelta = next_new_moon - previous_new_moon
    lunar_month_duration_days = lunar_month_duration.total_seconds() / SECONDS_IN_DAY

    # Current age of the Moon in this lunar month
    lunar_age = date - previous_new_moon
    lunar_age_days = lunar_age.total_seconds() / SECONDS_IN_DAY

    # Calculate the lunar day as a proportion of the lunar month
    lunar_day = lunar_age_days / (lunar_month_duration_days / 30)
    lunar_day = lunar_day % 30

    return int(lunar_day) + 1

async def calculate_main_lunar_day(date: datetime) -> int:
    """
    Вычисляет основной лунный день для заданного времени и местоположения.

    Args:
        date (datetime): Дата, для которой нужно вычислить лунный день.
        longitude (float): Долгота местоположения.
        latitude (float): Широта местоположения.

    Returns:
        int: Основной лунный день.
    """
    midnight_lunar_day = get_lunar_day(date)
    noon_lunar_day = get_lunar_day(date + timedelta(hours=12))
    
    return midnight_lunar_day if midnight_lunar_day == noon_lunar_day else noon_lunar_day

def find_lunar_day_transition(
    lunar_day: int,
    date: datetime, 
) -> Optional[datetime]:
    """
    Находит время перехода на следующий лунный день.

    Args:
        lunar_day (int): Текущий лунный день.
        date (datetime): Дата для начала поиска.
        longitude (float): Долгота местоположения.
        latitude (float): Широта местоположения.

    Returns:
        Optional[datetime]: Время перехода на следующий лунный день, если оно найдено.
    """
    start_search_time = date + timedelta(hours=12)

    for hour in range(1, 25):
        next_check_time = start_search_time + timedelta(hours=hour)
        if get_lunar_day(next_check_time) != lunar_day:
            start_time = next_check_time - timedelta(hours=1)
            end_time = next_check_time 

            while end_time - start_time > timedelta(minutes=1):
                mid_time = start_time + (end_time - start_time) / 2
                if get_lunar_day(mid_time) == lunar_day:
                    start_time = mid_time
                else:
                    end_time = mid_time
            return end_time

    return None


def get_moon_sign(date: datetime):
    # Определение положения Луны
    moon = ephem.Moon(date)
    ecliptic_long = ephem.Ecliptic(moon).lon

    # Определение зодиакального созвездия для Луны
    ecliptic_long_deg = ecliptic_long * 180 / ephem.pi  # Перевод в градусы
    for i, bound in enumerate(ZODIAC_BOUNDS):
        if ecliptic_long_deg < bound:
            return ZODIAC_SIGNS[i - 1] if i > 0 else ZODIAC_SIGNS[-1]


def get_moon_signs_at_date(
    date: datetime, 
    timezone_offset: int
) -> dict:
    date = date.replace(hour=0, minute=0)

    start_of_day = date + timedelta(hours=timezone_offset)
    end_of_day = start_of_day + timedelta(hours=23, minutes=58)
    
    start_sign = get_moon_sign(start_of_day)
    end_sign = get_moon_sign(end_of_day)
    
    result = {
        "start_sign": start_sign
    }
    
    if start_sign != end_sign:
        # Бинарный поиск времени смены знака
        left_time = start_of_day
        right_time = end_of_day

        while right_time - left_time > timedelta(minutes=1):  # пока разница во времени больше минуты
            middle_time = left_time + (right_time - left_time) / 2
            if get_moon_sign(middle_time) == start_sign:
                left_time = middle_time
            else:
                right_time = middle_time

        change_time = left_time

        result["change_time"] = change_time.strftime(TIME_FORMAT)
        result["end_sign"] = end_sign
    
    return result


def get_moon_phase(observer: ephem.Observer) -> MoonPhase:
    moon = ephem.Moon()
    moon.compute(observer)
    current_phase = moon.moon_phase

    for (start, end), phase in MOON_PHASES_RANGES.items():
        if not (start <= current_phase <= end):
            continue
        
        if 0.05 < current_phase < 0.95:
            # Вычисляем процент освещенности за 6 часов до текущего момента
            observer.date = observer.date.datetime() - timedelta(hours=6)
            moon.compute(observer)
            past_phase = moon.moon_phase

            # Определяем, растущая или убывающая фаза
            is_waxing = current_phase > past_phase

            return phase[0] if is_waxing else phase[1]
    else:
        logging.error(
            f'get_moon_phase Нет подходящего диапазона для текущего лунного освещения - {current_phase}'
        )
        return MoonPhase.NEW_MOON

