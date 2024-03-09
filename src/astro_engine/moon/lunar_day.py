import logging
import ephem

from datetime import datetime, timedelta

from src import config
from ..models import LunarDay


# Константы
SECONDS_IN_DAY = 24 * 60 * 60

ISO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT: str = config.get("database.time_format")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

LOGGER = logging.getLogger(__name__)


def get_main_lunar_day_at_date(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Определяет лунный день, который занимает наибольшее количество
    времени в течение указанной даты.
    """
    midnight_lunar_day = _get_lunar_day(utcdate, longitude, latitude)
    noon_lunar_day = _get_lunar_day(
        utcdate + timedelta(hours=12),
        longitude,
        latitude
    )
    next_midnight_lunar_day = _get_lunar_day(
        utcdate + timedelta(hours=24),
        longitude,
        latitude
    )

    one_lunar_day_from_midnight_to_noon = (
        midnight_lunar_day.number == noon_lunar_day.number
    )
    one_lunar_day_from_noon_to_next_midnight = (
        next_midnight_lunar_day.number == noon_lunar_day.number
    )
    if one_lunar_day_from_midnight_to_noon:
        return midnight_lunar_day

    elif one_lunar_day_from_noon_to_next_midnight:
        return noon_lunar_day

    else:
        _get_main_lunar_day_when_3_lunar_days_at_date(utcdate, longitude, latitude)


def _get_main_lunar_day_when_3_lunar_days_at_date(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    lunar_days = []

    # 25, а не 24 чтобы учитывать последний час и избежать равнозначного
    # результата, когда каждый лунный день занимает по 8 часов.
    for hour in range(25):
        time_point = utcdate + timedelta(hours=hour)

        lunar_day = _get_lunar_day(time_point, longitude, latitude)
        lunar_days.append(lunar_day)

    # Сопоставление каждого лунного дня с его продолжительностью
    lunar_day_durations = {}
    for ld in lunar_days:
        if ld.number in lunar_day_durations:
            lunar_day_durations[
                ld.number
            ] += 1  # Увеличиваем продолжительность на единицу (час)
        else:
            lunar_day_durations[ld.number] = 1

    # Находим лунный день с максимальной продолжительностью
    most_common_lunar_day_number = max(
        lunar_day_durations,
        key=lunar_day_durations.get
    )

    # Находим соответствующий объект LunarDay
    for ld in lunar_days:
        if ld.number == most_common_lunar_day_number:
            return ld


def _get_lunar_day_end(utcdate: datetime, longitude: float, latitude: float) -> datetime:
    """
    Bычисляет время следующего восхода Луны или следующего новолуния после заданной даты и времени.
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


def _get_lunar_day_start(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> datetime:
    """
    Вычисляет время следующего восхода Луны или следующего новолуния после заданной даты и времени.

    Функция использует библиотеку `ephem` для расчета астрономических событий, таких как восходы Луны.
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


def _get_lunar_day_number(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> int:
    """
    Вычисляет лунный день для заданной даты и координат.

    Алгоритм работает следующим образом: он находит время последнего новолуния,
    затем вычисляет последовательность восходов Луны после этого новолуния до заданной даты.
    Номер лунного дня определяется как количество этих восходов.
    """
    # Нахождение времени последнего новолуния до заданной даты
    previous_new_moon = ephem.previous_new_moon(utcdate).datetime()

    # Создаем объект Observer для заданных координат и времени
    observer = ephem.Observer()
    observer.lat = str(latitude)
    observer.lon = str(longitude)

    # Инициализация счетчика восходов Луны
    lunar_day_count = 1
    current_time = previous_new_moon

    while current_time <= utcdate:
        observer.date = current_time
        moon = ephem.Moon(observer)
        next_moon_rise = observer.next_rising(moon).datetime().replace(tzinfo=None)

        # Проверяем, не вышла ли следующая дата восхода за пределы заданной даты
        if next_moon_rise > utcdate:
            break

        lunar_day_count += 1
        current_time = next_moon_rise

    return lunar_day_count


def _get_lunar_day(
    time_point: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Возвращает лунный день, который соответствует временной точке которую передали
    """
    lunar_day_number = _get_lunar_day_number(time_point, longitude, latitude)
    lunar_day_start = _get_lunar_day_start(time_point, longitude, latitude)
    lunar_day_end = _get_lunar_day_end(time_point, longitude, latitude)

    lunar_day = LunarDay(
        number=lunar_day_number,
        start=lunar_day_start,
        end=lunar_day_end
    )
    return lunar_day


def get_next_lunar_day(
    lunar_day: LunarDay,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Определяет следующий лунный день после заданного.
    """
    next_lunar_day_start = lunar_day.end + timedelta(minutes=10)
    lunar_day = _get_lunar_day(next_lunar_day_start, longitude, latitude)
    return lunar_day


def get_previous_lunar_day(
    lunar_day: LunarDay, longitude: float, latitude: float
) -> LunarDay:
    """
    Определяет предыдущий лунный день до заданного.
    """
    # Находим начало предыдущего лунного дня, которое является началом текущего минус одна минута
    previous_lunar_day_end = lunar_day.start - timedelta(minutes=10)

    lunar_day = _get_lunar_day(previous_lunar_day_end, longitude, latitude)
    return lunar_day
