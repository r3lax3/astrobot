import logging
from datetime import datetime, timedelta

from typing import List, Optional

from src import config
from src.enums import SwissEphPlanet

from .sign import get_moon_sign_period
from ..models import User, TimePeriod, MonoAstroEvent
from ..utils import get_juliday, get_planet_data

# Константы
LOGGER = logging.getLogger(__name__)
ORBIS = 0.1
ASPECTS = [0, 60, 90, 120, 180, 240, 270, 300]
DATETIME_FORMAT = config.get("database.datetime_format")


def get_blank_moon_period(
    date: datetime,
    user: User,
    timezone_offset: int
) -> TimePeriod:
    moon_sign_period = get_moon_sign_period(date, user)

    # LOGGER.info(
    #     '\nMoon sign period:\n\nstart: {start}\nend: {end}'.format(
    #         start=moon_sign_period.start.strftime(DATETIME_FORMAT),
    #         end=moon_sign_period.end.strftime(DATETIME_FORMAT)
    #     )
    # )

    latest_event_peak = _get_latest_event_peak(moon_sign_period, user)

    timezone_timedelta = timedelta(hours=timezone_offset)

    if latest_event_peak is None:
        start = moon_sign_period.start + timezone_timedelta,
        end = moon_sign_period.end + timezone_timedelta
    else:
        start = latest_event_peak + timezone_timedelta
        end = moon_sign_period.end + timezone_timedelta

    return TimePeriod(start, end)


def _get_latest_event_peak(
    moon_sign_period: TimePeriod,
    user
) -> datetime | None:
    astro_events = get_astro_events_from_period(
        moon_sign_period.start,
        moon_sign_period.end,
        user
    )

    astro_events_with_peaks = (
        event for event in astro_events
        if event.peak is not None
    )

    filtered_and_sorted_events = sorted(
        astro_events_with_peaks,
        key=lambda x: x.peak
    )

    if not filtered_and_sorted_events:
        return None

    latest_event_peak = filtered_and_sorted_events[-1].peak
    return latest_event_peak


def calculate_aspect(
    first_planet_pos: float,
    second_planet_pos: float
) -> Optional[int]:

    diff = abs(first_planet_pos - second_planet_pos) % 360
    for aspect in ASPECTS:
        if abs(diff - aspect) <= ORBIS:
            return aspect


def get_mono_astro_event_at_time(
    utcdate: datetime,
    user: User
) -> List[MonoAstroEvent]:
    events = []

    juliday = get_juliday(utcdate)

    planets_data = {
        planet: get_planet_data(juliday, planet, user.current_location)
        for planet in SwissEphPlanet
    }

    # logging.info(planets_data)

    moon_data = planets_data.pop(SwissEphPlanet.MOON)
    moon_pos = moon_data[0][0]

    for target_planet, planet_data in planets_data.items():
        target_planet_pos = planet_data[0][0]

        aspect_value = calculate_aspect(moon_pos, target_planet_pos)
        if aspect_value is not None:
            events.append(
                MonoAstroEvent(
                    first_planet=SwissEphPlanet.MOON,
                    second_planet=target_planet,
                    aspect=aspect_value,
                    peak=utcdate,
                )
            )

    return events


def get_astro_events_from_period(
    start: datetime,
    finish: datetime,
    user: User
) -> List[MonoAstroEvent]:
    """
    Получает уникальные и отсортированные астрологические события в указанный период времени.

    Аргументы:
    - start: datetime — начальное время периода.
    - finish: datetime — конечное время периода.
    - user: User — объект пользователя, для которого ищутся события.

    Возвращает список уникальных и отсортированных событий (List[MonoAstroEvent]).
    """

    step = timedelta(minutes=10)
    current_time = start

    all_events = []

    while current_time <= finish:
        events_at_current_time = get_mono_astro_event_at_time(
            current_time,
            user
        )
        all_events.extend(events_at_current_time)
        current_time += step

    unique_events = remove_duplicates(all_events)
    unique_sorted_events = sort_mono_astro_events(unique_events)

    return unique_sorted_events
    # return all_events


def sort_mono_astro_events(events: List[MonoAstroEvent]):
    """
    Сортирует астрологические события по времени пика, разделяя события с пиком и без.

    Аргументы:
    - events: List[MonoAstroEvent] — список астрологических событий для сортировки.

    Возвращает отсортированный список событий, где сначала идут события без указанного пика,
    а затем события с указанным временем пика, отсортированные по времени пика.
    """

    events_with_peak = remove_duplicates(
        [event for event in events if event.peak is not None]
    )
    events_without_peak = remove_duplicates(
        [event for event in events if event.peak is None]
    )

    sorted_events_with_peak = sorted(
        events_with_peak,
        key=lambda x: x.peak
    )

    return events_without_peak + sorted_events_with_peak


def remove_duplicates(events: List[MonoAstroEvent]) -> List[MonoAstroEvent]:
    """
    Удаляет дубликаты астрологических событий из списка, сначала сортируя их.

    Аргументы:
    - events: List[MonoAstroEvent] — список событий для удаления дубликатов.

    Возвращает список уникальных астрологических событий.
    """

    events_sorted = sorted(
        events,
        key=lambda x: (x.first_planet, x.second_planet, x.aspect, x.peak)
    )
    unique_events = calculate_average_peak(events_sorted)

    return unique_events


def calculate_average_peak(
    events: List[MonoAstroEvent]
) -> List[MonoAstroEvent]:
    """
    Рассчитывает среднее время пика для группы событий, которые происходят в течение 15 минут.

    Аргументы:
    - events: List[MonoAstroEvent] — отсортированный список событий для расчёта.

    Возвращает список событий с усреднённым временем пика для близко происходящих событий.

    п. А.

    Не трогай

    Работает при помощи магии и заговора тибетского шамана Абуарубубдрара
    """
    temp_group_for_same_events = [events[0]] if events else []
    return_events_list = []

    for current_event in events[1:]:
        current_event_key = (
            current_event.first_planet,
            current_event.second_planet,
            current_event.aspect
        )

        last_event = temp_group_for_same_events[-1]
        last_event_key = (
            last_event.first_planet,
            last_event.second_planet,
            last_event.aspect
        )

        current_and_last_event_same = current_event_key == last_event_key

        peak_diff = current_event.peak - last_event.peak
        peak_diff_lower_15_min = peak_diff <= timedelta(minutes=15)

        if current_and_last_event_same and peak_diff_lower_15_min:
            temp_group_for_same_events.append(current_event)

        else:
            if temp_group_for_same_events:
                avg_peak_datetime = calculate_average_peak_for_temp_group(
                    temp_group_for_same_events
                )
                return_events_list.append(
                    MonoAstroEvent(
                        temp_group_for_same_events[0].first_planet,
                        temp_group_for_same_events[0].second_planet,
                        temp_group_for_same_events[0].aspect,
                        avg_peak_datetime
                    )
                )
                temp_group_for_same_events = [current_event]

    if temp_group_for_same_events:
        avg_peak_datetime = calculate_average_peak_for_temp_group(
            temp_group_for_same_events
        )
        return_events_list.append(
            MonoAstroEvent(
                temp_group_for_same_events[0].first_planet,
                temp_group_for_same_events[0].second_planet,
                temp_group_for_same_events[0].aspect,
                avg_peak_datetime
            )
        )
    return return_events_list


def calculate_average_peak_for_temp_group(
    temp_group: List[MonoAstroEvent]
) -> datetime:
    """
    Вычисляет среднее время пика для временной группы событий.

    Аргументы:
    - temp_group: List[MonoAstroEvent] — группа событий для расчёта среднего времени пика.

    Возвращает datetime с усреднённым временем пика для группы событий.
    """
    timestamp_list = (event.peak.timestamp() for event in temp_group)
    avg_peak_timestamp = sum(timestamp_list) / len(temp_group)

    return datetime.fromtimestamp(avg_peak_timestamp)
