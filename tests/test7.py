import ephem

from datetime import datetime, timedelta
from dataclasses import dataclass


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
    # Находим начало следующего лунного дня, которое является концом 
    # текущего + маленький интервал самого восхода
    next_lunar_day_start = lunar_day.end + timedelta(minutes=10)

    # Получаем данные следующего лунного дня
    next_lunar_day_number = get_lunar_day_number(next_lunar_day_start, longitude, latitude)
    next_lunar_day_end = get_lunar_day_end(next_lunar_day_start, longitude, latitude)

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
    previous_lunar_day_end = lunar_day.start - timedelta(minutes=10)

    # Получаем данные предыдущего лунного дня
    previous_lunar_day_number = get_lunar_day_number(previous_lunar_day_end, longitude, latitude)
    previous_lunar_day_start = get_lunar_day_start(previous_lunar_day_end, longitude, latitude)

    return LunarDay(
        number=previous_lunar_day_number, 
        start=previous_lunar_day_start,
        end=previous_lunar_day_end
    )


# Функция для вывода переходов между лунными днями
def print_lunar_day_transitions(
    start_date: datetime, 
    end_date: datetime, 
    longitude: float, 
    latitude: float
):
    current_date = start_date
    while current_date <= end_date:
        lunar_day = get_lunar_day(current_date, longitude, latitude)
        print(f"С {current_date.strftime('%Y.%m.%d, %H:%M')} {lunar_day.number}-й лунный день")
        # Переходим к следующему лунному дню
        current_date = lunar_day.end + timedelta(minutes=1)

# Задаем начальную и конечную дату для тестирования
start_date = datetime(2023, 8, 1, 0, 0)
end_date = datetime(2023, 12, 29, 23, 59)

# Координаты Москвы
longitude = 37.6173
latitude = 55.7558

# Вывод переходов между лунными днями
print_lunar_day_transitions(start_date, end_date, longitude, latitude)

