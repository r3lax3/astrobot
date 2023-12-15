import logging
import ephem
import swisseph as swe

from datetime import datetime, timedelta
from typing import Union, Dict

from src import config
from src.enums import MoonPhase, ZodiacSign, SwissEphPlanet
from src.astro_engine.models import LunarDay, Location


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
    ZodiacSign.PISCES
]

MOON_PHASES_RANGES = {
    (0, 0.05): MoonPhase.NEW_MOON,
    (0.05, 0.45): (MoonPhase.WAXING_CRESCENT, MoonPhase.WANING_CRESCENT),
    (0.45, 0.55): (MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER),
    (0.55, 0.95): (MoonPhase.WAXING_GIBBOUS, MoonPhase.WANING_GIBBOUS),
    (0.95, 1): MoonPhase.FULL_MOON,
}
ISO_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT: str = config.get('database.time_format')



def get_juliday(utc_date: datetime) -> float:
    """Calculates julian day from the utc time."""
    utc_time = utc_date.hour + utc_date.minute / 60
    julian_day = float(swe.julday(utc_date.year, utc_date.month, utc_date.day, utc_time))
    return julian_day

def calculate_moon_degrees_ut(juliday: float, location: Location):
    # Установка топографических координат наблюдателя
    swe.set_topo(location.longitude, location.latitude, 0)

    flag = swe.FLG_SWIEPH + swe.FLG_SPEED + swe.FLG_TOPOCTR
    return swe.calc(juliday, SwissEphPlanet.MOON.value, flag)[0][0]

def calculate_moon_sign(moon_degrees: float) -> ZodiacSign:
    for i, bound in enumerate(ZODIAC_BOUNDS):
        if moon_degrees < bound:
            return ZODIAC_SIGNS[i]
    else:
        return ZODIAC_SIGNS[-1]

def get_moon_sign(date: datetime, location: Location) -> ZodiacSign:
    juliday = get_juliday(date)
    moon_degree = calculate_moon_degrees_ut(juliday, location)
    return calculate_moon_sign(moon_degree)


def get_moon_signs_at_date(
    date: datetime,
    timezone_offset: int,
    location: Location
) -> Dict[str, Union[ZodiacSign, str]]:
    """
    Определяет зодиакальный знак Луны на начало и конец заданной даты.

    Args:
        date (datetime): Дата для расчёта.
        timezone_offset (int): Смещение временной зоны.

    Returns:
        dict: Словарь с знаками Луны и временем смены знака.
    """
    date = date.replace(hour=0, minute=0)
    start_of_day = date + timedelta(hours=timezone_offset)
    end_of_day = start_of_day + timedelta(hours=23, minutes=58)

    start_sign = get_moon_sign(start_of_day, location)
    end_sign = get_moon_sign(end_of_day, location)
    
    result = {"start_sign": start_sign}
    
    if start_sign != end_sign:
        left_time, right_time = start_of_day, end_of_day
        while right_time - left_time > timedelta(minutes=1):
            middle_time = left_time + (right_time - left_time) / 2
            if get_moon_sign(middle_time, location) == start_sign:
                left_time = middle_time
            else:
                right_time = middle_time
        change_time = left_time
        result.update(
            {
                "change_time": change_time.strftime(TIME_FORMAT),
                "end_sign": end_sign
            }
        )
    
    return result


def get_moon_phase(utcdate: datetime, longitude: float, latitude: float) -> MoonPhase:
    """
    Вычисляет фазу Луны для заданной даты и координат.

    Args:
        date (datetime): Дата для расчёта.
        longitude (float): Долгота местоположения.
        latitude (float): Широта местоположения.

    Returns:
        MoonPhase: Фаза Луны.
    """
    observer = ephem.Observer()
    observer.date = utcdate
    observer.lon = str(longitude)
    observer.lat = str(latitude)

    moon = ephem.Moon(observer)
    current_phase = moon.moon_phase

    for (start, end), phase in MOON_PHASES_RANGES.items():
        if start <= current_phase <= end:
            if isinstance(phase, tuple):
                # Определение растущей или убывающей фазы Луны
                observer.date = observer.date.datetime() - timedelta(hours=6) # Смещение на 6 часов назад
                moon.compute(observer)
                is_waxing = current_phase > moon.moon_phase
                return phase[0] if is_waxing else phase[1]
            else:
                return phase
    logging.error(f'get_moon_phase: No suitable range for current phase - {current_phase}')
    return MoonPhase.NEW_MOON


def get_lunar_day_end(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> datetime:
    """
    Dычисляет время следующего восхода Луны или следующего новолуния после заданной даты и времени.

    Функция использует библиотеку `ephem` для расчета астрономических событий, таких как восходы Луны.
    
    Args:
        utcdate (datetime): Дата и время для начала расчета.
        longitude (float): Долгота наблюдателя.
        latitude (float): Широта наблюдателя.

    Returns:
        datetime: Время следующего восхода Луны или следующего новолуния.
    """
    # Создаем объект Observer для заданных координат и времени
    observer = ephem.Observer()
    observer.lat = str(latitude)  # Преобразование широты в строку
    observer.lon = str(longitude)  # Преобразование долготы в строку
    observer.date = utcdate  # Установка начальной даты и времени для расчетов

    # Получение объекта Луны для расчетов
    moon = ephem.Moon(observer)
    # Расчет времени следующего восхода Луны
    moon_rise = observer.next_rising(moon).datetime().replace(tzinfo=None)
    
    # Расчет времени следующего новолуния
    next_new_moon = ephem.next_new_moon(utcdate).datetime()

    # Возвращаем время следующего восхода Луны, если оно раньше времени следующего новолуния
    # В противном случае возвращаем время следующего новолуния
    return moon_rise if moon_rise < next_new_moon else next_new_moon


def get_lunar_day_start(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> datetime:
    """
    Вычисляет время следующего восхода Луны или следующего новолуния после заданной даты и времени.

    Функция использует библиотеку `ephem` для расчета астрономических событий, таких как восходы Луны.
    
    Args:
        utcdate (datetime): Дата и время для начала расчета.
        longitude (float): Долгота наблюдателя.
        latitude (float): Широта наблюдателя.

    Returns:
        datetime: Время следующего восхода Луны или следующего новолуния.
    """
    # Создаем объект Observer для заданных координат и времени
    observer = ephem.Observer()
    observer.lat = str(latitude)  # Преобразование широты в строку
    observer.lon = str(longitude)  # Преобразование долготы в строку
    observer.date = utcdate  # Установка начальной даты и времени для расчетов

    # Получение объекта Луны для расчетов
    moon = ephem.Moon(observer)
    # Расчет времени следующего восхода Луны
    moon_rise = observer.previous_rising(moon).datetime().replace(tzinfo=None)
    
    # Расчет времени следующего новолуния
    previous_new_moon = ephem.previous_new_moon(utcdate).datetime()

    # Возвращаем время следующего восхода Луны, если оно раньше времени следующего новолуния
    # В противном случае возвращаем время следующего новолуния
    return moon_rise if moon_rise < previous_new_moon else previous_new_moon


def get_lunar_day_number(utcdate: datetime, longitude: float, latitude: float) -> int:
    """
    Вычисляет лунный день для заданной даты и координат.

    Алгоритм работает следующим образом: он находит время последнего новолуния,
    затем вычисляет последовательность восходов Луны после этого новолуния до заданной даты.
    Номер лунного дня определяется как количество этих восходов.

    Args:
        utcdate (datetime): Дата для расчёта.
        longitude (float): Долгота местоположения.
        latitude (float): Широта местоположения.

    Returns:
        int: Лунный день.
    """
    # Нахождение времени последнего новолуния до заданной даты
    previous_new_moon = ephem.previous_new_moon(utcdate).datetime()

    # Получение времени первого восхода Луны после последнего новолуния
    first_moon_rise_after_new_moon = get_lunar_day_end(previous_new_moon, longitude, latitude)

    # Инициализация списка восходов Луны с первым восходом
    moon_rises = [first_moon_rise_after_new_moon]

    # Цикл для вычисления всех восходов Луны после последнего новолуния до заданной даты
    while utcdate - moon_rises[-1] > timedelta(minutes=15) and utcdate > moon_rises[-1]:
        # Вычисление времени следующего восхода Луны
        next_search_time = moon_rises[-1] + timedelta(minutes=5)
        next_moon_rise = get_lunar_day_end(next_search_time, longitude, latitude)
        moon_rises.append(next_moon_rise)

    # Вычисление номера лунного дня
    # Используется модульная арифметика для цикличного счета дней от 1 до 30
    return len(moon_rises)


def get_lunar_day(
    time_point: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    lunar_day_number = get_lunar_day_number(time_point, longitude, latitude)
    lunar_day_start = get_lunar_day_start(time_point, longitude, latitude)
    lunar_day_end = get_lunar_day_end(time_point, longitude, latitude) 

    lunar_day = LunarDay(number=lunar_day_number, start=lunar_day_start, end=lunar_day_end)
    return lunar_day


def get_main_lunar_day_at_date(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Определяет лунный день, который занимает наибольшее количество времени в течение указанной даты.

    Args:
        utcdate (datetime): Дата для расчета (в UTC). Нужно передавать точку начала дня
        longitude (float): Долгота наблюдателя.
        latitude (float): Широта наблюдателя.

    Returns:
        int: Номер лунного дня, который занимает наибольшее количество времени в указанную дату.
    """

    midnight_lunar_day = get_lunar_day(utcdate, longitude, latitude)
    noon_lunar_day = get_lunar_day(utcdate + timedelta(hours=12), longitude, latitude)
    next_midnight_lunar_day = get_lunar_day(utcdate + timedelta(hours=24), longitude, latitude)

    # Один лунный день 00:00 -> 12:00
    if midnight_lunar_day.number == noon_lunar_day.number:
        return midnight_lunar_day
    # Один лунный день 12:00 -> 24:00
    if noon_lunar_day.number == next_midnight_lunar_day.number:
        return noon_lunar_day

    # Если же в один день входит 3 разных лунных дня, то нужен другой подход

    # Инициализация списка для хранения объектов LunarDay за каждый час
    lunar_days = []

    # Разбиваем день на 25 интервалов (по одному часу каждый)

    # 25, а не 24 чтобы учитывать последний час и избежать равнозначного 
    # результата, когда каждый лунный день занимает по 8 часов. 
    for hour in range(25):
        # Вычисляем временную метку для каждого часа
        time_point = utcdate + timedelta(hours=hour)

        # Получаем номер лунного дня для каждого часа
        lunar_day_number = get_lunar_day_number(time_point, longitude, latitude)
        lunar_day_start = get_lunar_day_start(time_point, longitude, latitude)
        lunar_day_end = get_lunar_day_end(time_point, longitude, latitude) 

        lunar_day = LunarDay(number=lunar_day_number, start=lunar_day_start, end=lunar_day_end)
        lunar_days.append(lunar_day)

    # Сопоставление каждого лунного дня с его продолжительностью
    lunar_day_durations = {}
    for ld in lunar_days:
        if ld.number in lunar_day_durations:
            lunar_day_durations[ld.number] += 1 # Увеличиваем продолжительность на единицу (час)
        else:
            lunar_day_durations[ld.number] = 1

    # Находим лунный день с максимальной продолжительностью
    most_common_lunar_day_number = max(lunar_day_durations, key=lunar_day_durations.get)

    # Находим соответствующий объект LunarDay
    for ld in lunar_days:
        if ld.number == most_common_lunar_day_number:
            return ld

def get_next_lunar_day(lunar_day: LunarDay, longitude: float, latitude: float) -> LunarDay:
    """
    Определяет следующий лунный день после заданного.

    Args:
        lunar_day (LunarDay): Текущий лунный день.
        longitude (float): Долгота местоположения.
        latitude (float): Широта местоположения.

    Returns:
        LunarDay: Следующий лунный день.
    """
    # Находим начало следующего лунного дня, которое является концом текущего
    next_lunar_day_start = lunar_day.end

    # Получаем данные следующего лунного дня
    time_point = next_lunar_day_start + timedelta(minutes=10)

    next_lunar_day_number = get_lunar_day_number(time_point, longitude, latitude)
    next_lunar_day_end = get_lunar_day_end(time_point, longitude, latitude)

    return LunarDay(
        number=next_lunar_day_number,
        start=next_lunar_day_start,
        end=next_lunar_day_end
    )


def get_previous_lunar_day(lunar_day: LunarDay, longitude: float, latitude: float) -> LunarDay:
    """
    Определяет предыдущий лунный день до заданного.

    Args:
        lunar_day (LunarDay): Текущий лунный день.
        longitude (float): Долгота местоположения.
        latitude (float): Широта местоположения.

    Returns:
        LunarDay: Предыдущий лунный день.
    """
    # Находим начало предыдущего лунного дня, которое является началом текущего минус одна минута
    previous_lunar_day_end = lunar_day.start - timedelta(minutes=1)

    # Получаем данные предыдущего лунного дня
    previous_lunar_day_number = get_lunar_day_number(previous_lunar_day_end, longitude, latitude)
    previous_lunar_day_start = get_lunar_day_start(previous_lunar_day_end, longitude, latitude)

    return LunarDay(
        number=previous_lunar_day_number, 
        start=previous_lunar_day_start,
        end=previous_lunar_day_end
    )

