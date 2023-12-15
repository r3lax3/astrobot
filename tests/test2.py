import ephem

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
    print(f'get_lunar_day_end: moon_rise={moon_rise.strftime(READABLE_DATETIME_FORMAT)}')

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

def get_lunar_days_for_last_30_days(longitude: float, latitude: float):
    end_date = datetime.utcnow() + timedelta(1)
    start_date = end_date - timedelta(days=3)

    current_moonrise = get_lunar_day_end(start_date, longitude, latitude)

    while current_moonrise < end_date:
        try:
            next_moonrise = get_lunar_day_end(current_moonrise + timedelta(minutes=5), longitude, latitude)

            readable_next_moonrise = (
                next_moonrise + timedelta(hours=10)
            ).strftime(READABLE_DATETIME_FORMAT)
            lunar_day = get_lunar_day(next_moonrise, longitude, latitude)
            if lunar_day == 1:
                current_moonrise = ephem.previous_new_moon(next_moonrise).datetime()
            current_moonrise_str = (
                current_moonrise + timedelta(hours=10)
            ).strftime(READABLE_DATETIME_FORMAT)

            lunar_day_str = f"{lunar_day.number} Лунный день {current_moonrise_str} по {readable_next_moonrise}"
            print(lunar_day_str)
            current_moonrise = next_moonrise

        except (ephem.NeverUpError, ephem.AlwaysUpError):
            current_moonrise += timedelta(hours=2)


# Пример использования
longitude = 37.39936160219869  # Пример долготы
latitude = 55.87392997771667  # Пример широты

get_lunar_days_for_last_30_days(longitude, latitude)



# # Записываем начальное время
# now = datetime.utcnow()
# start_time = time.time()
#
# lunar_day = get_lunar_day(now, longitude, latitude)
#
# end_time = time.time()
#
# # Вычисляем и выводим время выполнения
# execution_time = end_time - start_time
# print(f"На дату {now.strftime(READABLE_DATETIME_FORMAT)} приходится {lunar_day} Лунный день")
# print(f"Время выполнения: {execution_time:.3f} секунд")



# timezone_str = get_timezone_str_from_coords(longitude, latitude)
# previous_new_moon = ephem.previous_new_moon(now).datetime() + timedelta(hours=3)
# previous_new_moon_str = previous_new_moon.strftime(READABLE_DATETIME_FORMAT)
# target_date = previous_new_moon + timedelta(minutes=30)
#
# moon_day = 1
# moon_day_moonrise = previous_new_moon
#
# print(f'С {moon_day_moonrise.strftime("%d.%m.%Y %H:%M")} {moon_day} Лунный день')
#
# while target_date < now:
#
#     target_date_moonrise = (get_next_moonrise(target_date, longitude, latitude) + timedelta(hours=1))
#
#     if target_date_moonrise - moon_day_moonrise > timedelta(minutes=30):
#         moon_day_moonrise = target_date_moonrise
#         moon_day += 1
#         print(f'С {moon_day_moonrise.strftime("%d.%m.%Y %H:%M")} {moon_day} Лунный день')
#
#     target_date += timedelta(hours=1)
#
