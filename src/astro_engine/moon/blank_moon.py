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

    LOGGER.info(
        '\nMoon sign period:\n\nstart: {start}\nend: {end}'.format(
            start=moon_sign_period.start.strftime(DATETIME_FORMAT),
            end=moon_sign_period.end.strftime(DATETIME_FORMAT)
        )
    )

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
    user: User
) -> datetime | None:
    """
    Находит время последнего точного аспекта луны в периоде знака.
    """
    events = get_astro_events_from_period(
        moon_sign_period.start,
        moon_sign_period.end,
        user
    )

    events_with_peak = [e for e in events if e.peak is not None]

    if not events_with_peak:
        return None

    latest_event = max(events_with_peak, key=lambda e: e.peak)  # type: ignore
    return latest_event.peak


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
    step = timedelta(minutes=10)
    current_time = start

    raw_events_list = []

    while current_time <= finish:
        events_at_current_time = get_mono_astro_event_at_time(
            current_time,
            user
        )
        raw_events_list.extend(events_at_current_time)
        current_time += step

    events = parse_events(raw_events_list)

    return events
    # return all_events


def sort_mono_astro_events(events: List[MonoAstroEvent]):
    """
    Сортирует астрологические события по времени пика, разделяя события с пиком и без.

    Аргументы:
    - events: List[MonoAstroEvent] — список астрологических событий для сортировки.

    Возвращает отсортированный список событий, где сначала идут события без указанного пика,
    а затем события с указанным временем пика, отсортированные по времени пика.
    """

    events_with_peak = parse_events(
        [event for event in events if event.peak is not None]
    )
    events_without_peak = parse_events(
        [event for event in events if event.peak is None]
    )

    events_with_peak.sort(key=lambda x: x.peak)  # type: ignore

    return events_without_peak + events_with_peak


def parse_events(events: List[MonoAstroEvent]) -> List[MonoAstroEvent]:
    """
    Убирает дубликаты астрологических событий.

    События без пика (peak=None) — просто факт наличия аспекта в периоде.
    Оставляем по одному на каждую комбинацию планет+аспект.

    События с пиком — конкретные моменты. Если несколько пиков одного
    аспекта идут подряд с разницей меньше часа, склеиваем их в один,
    беря середину интервала как новый пик.
    """
    if not events:
        return []

    events_without_peak = [e for e in events if e.peak is None]
    events_with_peak = [e for e in events if e.peak is not None]

    unique_events_without_peak = deduplicate_by_aspect(events_without_peak)
    merged_events_with_peak = merge_close_peaks(events_with_peak)

    return unique_events_without_peak + merged_events_with_peak


def get_aspect_signature(event: MonoAstroEvent) -> tuple:
    """Уникальный идентификатор аспекта (без учёта времени)."""
    return (event.first_planet, event.second_planet, event.aspect)


def deduplicate_by_aspect(events: List[MonoAstroEvent]) -> List[MonoAstroEvent]:
    """Оставляет по одному событию на каждую комбинацию планет+аспект."""
    seen = {}
    for event in events:
        signature = get_aspect_signature(event)
        if signature not in seen:
            seen[signature] = event
    return list(seen.values())


def merge_close_peaks(
    events: List[MonoAstroEvent],
    max_gap_between_peaks = timedelta(hours=1)
) -> List[MonoAstroEvent]:
    """
    Склеивает события одного аспекта, если их пики ближе часа друг к другу.
    Результат сортируется по времени пика.
    """
    if not events:
        return []


    # группируем по аспекту, внутри группы сортируем по времени
    events_sorted = sorted(events, key=lambda e: (get_aspect_signature(e), e.peak))

    result = []

    current_signature = None
    cluster_start = None
    cluster_end = None

    for event in events_sorted:
        signature = get_aspect_signature(event)

        is_same_aspect = (signature == current_signature)
        is_close_in_time = (
            cluster_end is not None
            and (event.peak - cluster_end) <= max_gap_between_peaks
        )

        if is_same_aspect and is_close_in_time:
            # расширяем текущий кластер
            cluster_end = event.peak
        else:
            # сохраняем предыдущий кластер (если был)
            if current_signature is not None:
                merged_event = create_event_with_middle_peak(
                    current_signature,
                    cluster_start,
                    cluster_end
                )
                result.append(merged_event)

            # начинаем новый кластер
            current_signature = signature
            cluster_start = event.peak
            cluster_end = event.peak

    # не забываем последний кластер
    if current_signature is not None:
        merged_event = create_event_with_middle_peak(
            current_signature,
            cluster_start,
            cluster_end
        )
        result.append(merged_event)

    return sorted(result, key=lambda e: e.peak)


def create_event_with_middle_peak(
    signature: tuple,
    start: datetime,
    end: datetime
) -> MonoAstroEvent:
    """Создаёт событие с пиком посередине между start и end."""
    middle = start + (end - start) / 2
    first_planet, second_planet, aspect = signature

    event = MonoAstroEvent(first_planet, second_planet, aspect, middle)
    print(f"event {event.first_planet} - {event.second_planet}, {event.aspect}")
    print(f"{start.strftime("%d/%m/%Y, %H:%M:%S")} -> {end.strftime("%d/%m/%Y, %H:%M:%S")}\n")
    return event

