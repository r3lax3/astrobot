import logging
from datetime import date, datetime, timedelta
from typing import Dict, Union, Literal

import ephem
import swisseph as swe

from src import config
from src.enums import MoonPhase, SwissEphPlanet, ZodiacSign

from .models import Location, LunarDay, User, TimePeriod
from .predictions import get_astro_events_from_period


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

LOGGER = logging.getlogger(__name__)


def get_juliday(utcdate: datetime) -> float:
    """Calculates julian day from the utc time."""
    utctime = utcdate.hour + utcdate.minute / 60  # time in seconds
    julian_day = float(
        swe.julday(utcdate.year, utcdate.month, utcdate.day, utctime)
    )
    return julian_day


def calculate_moon_degrees_ut(juliday: float, location: Location):
    """
    Возвращает градус отклонения луны на заданых координатах и в определённое время
    """
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
    """
    Вычисляет знак луны для переданой точки времени и координат
    """
    juliday = get_juliday(date)
    moon_degree = calculate_moon_degrees_ut(juliday, location)
    return calculate_moon_sign(moon_degree)


def get_moon_signs_at_date(
    date: date,
    timezone_offset: int,
    location: Location
) -> Dict[str, Union[ZodiacSign, str]]:
    """
    Определяет зодиакальный знак Луны на начало и конец заданной даты.
    """
    date = datetime(date.year, date.month, date.day)
    start_of_day = date - timedelta(hours=timezone_offset)
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
                "change_time": (
                    change_time + timedelta(hours=timezone_offset)
                ).strftime(TIME_FORMAT),
                "end_sign": end_sign,
            }
        )

    return result


def get_moon_phase(date: date, longitude: float, latitude: float) -> MoonPhase:
    """
    Вычисляет фазу Луны для заданной даты и координат.
    """
    observer = ephem.Observer()
    observer.date = datetime(date.year, date.month, date.day)
    observer.lon = str(longitude)
    observer.lat = str(latitude)

    moon = ephem.Moon(observer)
    current_phase = moon.moon_phase

    for (start, end), phase in MOON_PHASES_RANGES.items():
        if start <= current_phase <= end:
            if isinstance(phase, tuple):
                # Определение растущей или убывающей фазы Луны
                observer.date = observer.date.datetime() - timedelta(
                    hours=6
                )  # Смещение на 6 часов назад
                moon.compute(observer)
                is_waxing = current_phase > moon.moon_phase
                return phase[0] if is_waxing else phase[1]
            else:
                return phase
    logging.error(
        f"get_moon_phase: No suitable range for current phase - {current_phase}"
    )
    return MoonPhase.NEW_MOON


def get_lunar_day_end(utcdate: datetime, longitude: float, latitude: float) -> datetime:
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


def get_lunar_day_start(
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


def get_lunar_day_number(
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


def get_lunar_day(
    time_point: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Возвращает лунный день, который соответствует временной точке которую передали
    """
    lunar_day_number = get_lunar_day_number(time_point, longitude, latitude)
    lunar_day_start = get_lunar_day_start(time_point, longitude, latitude)
    lunar_day_end = get_lunar_day_end(time_point, longitude, latitude)

    lunar_day = LunarDay(
        number=lunar_day_number,
        start=lunar_day_start,
        end=lunar_day_end
    )
    return lunar_day


def get_main_lunar_day_at_date(
    utcdate: datetime,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Определяет лунный день, который занимает наибольшее количество
    времени в течение указанной даты.
    """
    midnight_lunar_day = get_lunar_day(utcdate, longitude, latitude)
    noon_lunar_day = get_lunar_day(
        utcdate + timedelta(hours=12),
        longitude,
        latitude
    )
    next_midnight_lunar_day = get_lunar_day(
        utcdate + timedelta(hours=24), longitude, latitude
    )

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

        lunar_day = LunarDay(
            number=lunar_day_number,
            start=lunar_day_start,
            end=lunar_day_end
        )
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


def get_next_lunar_day(
    lunar_day: LunarDay,
    longitude: float,
    latitude: float
) -> LunarDay:
    """
    Определяет следующий лунный день после заданного.
    """
    # Находим начало следующего лунного дня, которое является концом
    # текущего + маленький интервал самого восхода
    next_lunar_day_start = lunar_day.end + timedelta(minutes=10)

    # Получаем данные следующего лунного дня
    next_lunar_day_number = get_lunar_day_number(
        next_lunar_day_start,
        longitude,
        latitude
    )
    next_lunar_day_end = get_lunar_day_end(
        next_lunar_day_start,
        longitude,
        latitude
    )

    return LunarDay(
        number=next_lunar_day_number,
        start=next_lunar_day_start,
        end=next_lunar_day_end
    )


def get_previous_lunar_day(
    lunar_day: LunarDay, longitude: float, latitude: float
) -> LunarDay:
    """
    Определяет предыдущий лунный день до заданного.
    """
    # Находим начало предыдущего лунного дня, которое является началом текущего минус одна минута
    previous_lunar_day_end = lunar_day.start - timedelta(minutes=10)

    # Получаем данные предыдущего лунного дня
    previous_lunar_day_number = get_lunar_day_number(
        previous_lunar_day_end,
        longitude,
        latitude
    )
    previous_lunar_day_start = get_lunar_day_start(
        previous_lunar_day_end,
        longitude,
        latitude
    )

    return LunarDay(
        number=previous_lunar_day_number,
        start=previous_lunar_day_start,
        end=previous_lunar_day_end,
    )


def get_blank_moon_period(
    date: datetime,
    user: User,
    timezone_offset: int
) -> TimePeriod:
    moon_sign_period = get_moon_sign_period(date, user)

    LOGGER.info(
        '\nMoon sign period:\n\nstart: {start}\nend: {end}'.format(
            start=moon_sign_period.start.strftime(DATETIME_FORMAT),
            end=moon_sign_period.end.strftime(DATETIME_FORMAT)
        )
    )

    latest_event_peak = get_latest_event_peak(moon_sign_period, user)

    timezone_timedelta = timedelta(hours=timezone_offset)

    if latest_event_peak is None:
        start = moon_sign_period.start + timezone_timedelta,
        end = moon_sign_period.end + timezone_timedelta
    else:
        start = latest_event_peak + timezone_timedelta
        end = moon_sign_period.end + timezone_timedelta

    return TimePeriod(start, end)


def get_latest_event_peak(
    moon_sign_period: TimePeriod,
    user
) -> datetime | None:
    astro_events = get_astro_events_from_period(
        moon_sign_period.start,
        moon_sign_period.end,
        user
    )

    astro_events_with_peaks = (
        event
        for event in astro_events
        if event.peak_at is not None
    )

    filtered_and_sorted_events = sorted(
        astro_events_with_peaks,
        key=lambda x: x.peak_at
    )

    if not filtered_and_sorted_events:
        return None

    latest_event_peak = filtered_and_sorted_events[-1].peak_at
    return latest_event_peak


def get_moon_sign_period(
    utcdate: datetime,
    user: User
) -> TimePeriod:

    start_time = find_moon_sign_start(utcdate, user)
    end_time = find_moon_sign_end(utcdate, user)

    return TimePeriod(start=start_time, end=end_time)


def find_moon_sign_start(utcdate: datetime, user: User) -> datetime:
    current_sign = get_moon_sign(utcdate, user.current_location)

    search_time = utcdate
    previous_sign = current_sign

    # Идем назад по времени до смены знака
    while previous_sign == current_sign:
        search_time -= timedelta(hours=1)
        previous_sign = get_moon_sign(search_time, user.current_location)

    return binary_search_for_sign_change(
        search_time,
        search_time + timedelta(hours=1),
        previous_sign,
        user,
        seeking='start'
    )


def find_moon_sign_end(utcdate: datetime, user: User) -> datetime:
    current_sign = get_moon_sign(utcdate, user.current_location)

    search_time = utcdate
    next_sign = current_sign

    # Идем вперед по времени до смены знака
    while next_sign == current_sign:
        search_time += timedelta(hours=1)
        next_sign = get_moon_sign(search_time, user.current_location)

    # Точное определение конца знака с помощью бинарного поиска
    return binary_search_for_sign_change(
        utcdate,
        search_time,
        current_sign,
        user,
        seeking='end'
    )


def binary_search_for_sign_change(
    start_time: datetime,
    end_time: datetime,
    current_sign: str,
    user: User,
    seeking: Literal['start', 'end']
) -> datetime:
    while end_time - start_time > timedelta(minutes=1):
        middle_time = start_time + (end_time - start_time) // 2
        middle_sign = get_moon_sign(middle_time, user.current_location)

        if seeking == 'start':
            if middle_sign == current_sign:
                # Если средняя точка все еще в текущем знаке, сдвигаем начало интервала вперед
                start_time = middle_time
            else:
                # Если средняя точка уже в другом знаке, сдвигаем конец интервала назад
                end_time = middle_time
        else:  # seeking == 'end'
            if middle_sign == current_sign:
                # Если средняя точка все еще в текущем знаке, сдвигаем начало интервала вперед
                start_time = middle_time
            else:
                # Если средняя точка уже в другом знаке, сдвигаем конец интервала назад
                end_time = middle_time

    return start_time if seeking == 'start' else end_time
