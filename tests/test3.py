import ephem
import timeit

from datetime import datetime, timedelta
from dataclasses import dataclass


READABLE_DATETIME_FORMAT = '%H:%M %d.%m.%Y'
ISO_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIMEZONE_MOSCOW = 'Europe/Moscow'


@dataclass
class LunarDay:
    number: int
    start: datetime
    end: datetime


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

def get_main_lunar_day(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> int:
    """
    Определяет лунный день, который занимает наибольшее количество времени в течение указанной даты.

    Args:
        utcdate (datetime): Дата для расчета (в UTC).
        longitude (float): Долгота наблюдателя.
        latitude (float): Широта наблюдателя.

    Returns:
        int: Номер лунного дня, который занимает наибольшее количество времени в указанную дату.
    """
    # Инициализация списка для хранения объектов LunarDay за каждый час
    lunar_days = []

    # Разбиваем день на 24 интервала (по одному часу каждый)
    for hour in range(24):
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

def measure_performance():
    # Время выполнения для одного вызова функции
    single_run_time = timeit.timeit(
        'get_main_lunar_day(utc_now, longitude, latitude)', 
        globals=globals(),
        number=1
    )

    return single_run_time


import ephem
from datetime import datetime, timedelta
from typing import List, Tuple

def get_moon_rises(latitude: float, longitude: float, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
    """
    Возвращает список восходов Луны за указанный период времени.

    :param latitude: Широта наблюдателя.
    :param longitude: Долгота наблюдателя.
    :param start_date: Начальная дата интересующего периода.
    :param end_date: Конечная дата интересующего периода.
    :return: Список кортежей с датами и временами восходов Луны.
    """
    observer = ephem.Observer()
    observer.lat, observer.lon = str(latitude), str(longitude)

    current_date = start_date
    moon_rises = []

    while current_date <= end_date:
        observer.date = current_date
        moon_rise = observer.next_rising(ephem.Moon(observer)).datetime().replace(tzinfo=None)
        moon_rises.append((current_date, moon_rise))
        current_date += timedelta(days=1)

    return moon_rises

# Пример использования
latitude = 55.7558  # Широта Москвы
longitude = 37.6173  # Долгота Москвы
start_date = datetime.utcnow() - timedelta(days=5)
end_date = start_date + timedelta(days=15)

moon_rises = get_moon_rises(latitude, longitude, start_date, end_date)
for date, rise_time in moon_rises:
    print(f"Date: {date.strftime('%Y.%m.%d')}, Moonrise: {rise_time.strftime('%H:%M')}")



# # Выполнение 100 измерений и расчет среднего времени
# longitude = 37.39936160219869  # Пример долготы
# latitude = 55.87392997771667   # Пример широты
# utc_now = datetime.utcnow()
#
# print(get_main_lunar_day(utc_now, longitude, latitude))
#

# longitude = 37.39936160219869  # Пример долготы
# latitude = 55.87392997771667  # Пример широты
#
#
# print(get_main_lunar_day(datetime.utcnow(), longitude, latitude))
