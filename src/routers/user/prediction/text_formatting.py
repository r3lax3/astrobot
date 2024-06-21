import asyncio
import csv
import logging
import datetime

from typing import List, Optional
from datetime import datetime, timedelta, date

from babel.dates import format_date

from src import config, messages
from src.database import crud
from src.database.models import User as DBUser
from src.dicts import PLANET_ID_TO_NAME_RU, SWISSEPH_PLANET_TO_UNIVERSAL_PLANET
from src.astro_engine.models import AstroEvent
from src.astro_engine.models import Location as PredictionLocation
from src.astro_engine.models import User as PredictionUser
from src.astro_engine.predictions import (
    get_astro_events_from_period,
    get_astro_events_from_period_with_duplicates
)
from src.routers.user.prediction.models import Interpretation
from src.common import DAY_SELECTION_DATABASE
from src.enums import SwissEphPlanet


def get_interpretations_dict():
    with open(
        "interpretations.csv",
        "r",
        newline="",
        encoding="utf-8"
    ) as file:
        interpretations = [row for row in csv.reader(file)]
        interpretations_dict = {}
        for interpretation in interpretations:
            interpretation[2] = int(interpretation[2])

            transit_planet = interpretation[0]
            natal_planet = interpretation[1]
            aspect = int(interpretation[2])
            general = interpretation[3]
            favorably = interpretation[4].strip() if interpretation[4] else None
            unfavorably = interpretation[5].strip() if interpretation[5] else None

            key = (natal_planet, transit_planet, aspect)
            interpretations_dict[key] = Interpretation(
                natal_planet,
                transit_planet,
                aspect,
                general,
                favorably,
                unfavorably
            )
    return interpretations_dict


DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
UNIVERSAL_DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT: str = config.get("database.time_format")

DAYS = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]
MONTHS = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

interpretations_dict = get_interpretations_dict()


def formatted_general_events(events: List[AstroEvent]) -> str:
    interpretations = []
    for event in events:
        transit_planet = PLANET_ID_TO_NAME_RU[event.transit_planet]
        natal_planet = PLANET_ID_TO_NAME_RU[event.natal_planet]

        interpretation = interpretations_dict.get(
            (natal_planet, transit_planet, event.aspect),
            None
        )

        if interpretation is None:
            interpretation = interpretations_dict.get(
                (natal_planet, transit_planet, event.aspect),
                None
            )

        if not interpretation:
            logging.info(
                messages.NO_INTERPRETATION.format(
                    transit_planet=transit_planet,
                    natal_planet=natal_planet,
                    aspect=event.aspect,
                )
            )
            continue
        interpretations.append(f"💫{interpretation.general}")
    return "\n\n".join(interpretations)


def formatted_moon_events(events: List[AstroEvent]):
    favorably = []
    unfavorably = []

    for event in events:
        transit_planet = PLANET_ID_TO_NAME_RU[event.transit_planet]
        natal_planet = PLANET_ID_TO_NAME_RU[event.natal_planet]
        aspect = event.aspect

        interpretation = interpretations_dict.get(
            (natal_planet, transit_planet, event.aspect), None
        )

        if interpretation is None:
            interpretation = interpretations_dict.get(
                (natal_planet, transit_planet, event.aspect), None
            )

        if not interpretation:
            logging.info(
                messages.NO_INTERPRETATION.format(
                    transit_planet=transit_planet,
                    natal_planet=natal_planet,
                    aspect=aspect,
                )
            )
            continue

        favorably.append(interpretation.favorably.strip())
        unfavorably.append(interpretation.unfavorably.strip())

    favorably = "\n".join(favorably)
    unfavorably = "\n".join(unfavorably)

    formatted_text = messages.FAVORABLE_AND_UNFAVORABLE.format(
        favorably=favorably,
        unfavorably=unfavorably
    )

    return formatted_text


def format_date_russian(date: datetime) -> str:
    # Словари с названиями дней недели и месяцев на русском языке

    # Форматирование даты
    day_name = DAYS[date.weekday()]
    day_num = date.day
    month_name = MONTHS[date.month - 1]

    return f"{day_name}, {day_num} {month_name}"


def filtered_and_formatted_prediction(user, date: date) -> str:
    birth_location = crud.get_location(user.birth_location_id)
    current_location = crud.get_location(user.current_location_id)

    prediction_user = PredictionUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=PredictionLocation(
            longitude=birth_location.longitude,
            latitude=birth_location.latitude
        ),
        current_location=PredictionLocation(
            longitude=current_location.longitude,
            latitude=current_location.latitude
        ),
    )
    date = datetime(date.year, date.month, date.day)
    astro_events = get_astro_events_from_period(
        start=date + timedelta(hours=3),
        finish=date + timedelta(hours=27),
        user=prediction_user,
    )

    start_of_day = date + timedelta(hours=6, minutes=30)
    middle_of_day = date + timedelta(hours=15, minutes=30)
    end_of_day = date + timedelta(hours=24, minutes=45)

    day_events = []
    first_half_moon_events = []
    second_half_moon_events = []
    for event in astro_events:
        interpretation = interpretations_dict.get(
            (
                PLANET_ID_TO_NAME_RU[event.natal_planet],
                PLANET_ID_TO_NAME_RU[event.transit_planet],
                event.aspect
            ),
            None
        )

        if interpretation is None:
            continue

        # Day events
        if interpretation.general:
            day_events.append(event)
            continue

        have_favouraly_and_unfavourably_text = (
            interpretation.favorably is not None
            and
            interpretation.unfavorably is not None
        )

        # Moon events
        if have_favouraly_and_unfavourably_text:
            if not event.peak_at:
                continue

            if start_of_day < event.peak_at < middle_of_day:
                first_half_moon_events.append(event)

            if middle_of_day < event.peak_at < end_of_day:
                second_half_moon_events.append(event)

    first_half_moon_events_formatted = (
        formatted_moon_events(first_half_moon_events)
        if first_half_moon_events
        else None
    )

    second_half_moon_events_formatted = (
        formatted_moon_events(second_half_moon_events)
        if second_half_moon_events
        else None
    )

    day_events_formatted = formatted_general_events(
        day_events
    ) if day_events else None

    # Date
    formatted_date = format_date_russian(date)
    texts = []

    recommendations_heading = messages.PREDICTION_RECOMENDATION_HEADING.format(
        name=user.name
    )

    if not day_events_formatted:
        if (
            second_half_moon_events_formatted is None
            and first_half_moon_events_formatted is None
        ):
            formatted_date_str = messages.PREDICTION_TEXT_FORMATTED_DATE.format(
                formatted_date=formatted_date
            )

            texts = [
                formatted_date_str,
                recommendations_heading,
                messages.PREDICTION_TEXT_NEUTRAL_BACKGROUND_TODAY,
                messages.USE_OTHER_FUNCTION_FOR_CORRECT_PLANNING,
            ]
        else:
            formatted_date_str = messages.PREDICTION_TEXT_FORMATTED_DATE.format(
                formatted_date=formatted_date
            )
            default_moon_sign_text = (
                messages.PREDICTION_TEXT_NEUTRAL_BACKGROUND
                + "\n\n"
                + messages.USE_OTHER_FUNCTION_FOR_CORRECT_PLANNING
            )
            moon_events = messages.PREDICTION_TEXT_MOON_EVENTS.format(
                first_half_moon_events=first_half_moon_events_formatted
                or default_moon_sign_text,
                second_half_moon_events=second_half_moon_events_formatted
                or default_moon_sign_text,
            )

            texts = [
                formatted_date_str,
                recommendations_heading,
                moon_events
            ]
    else:
        if (
            second_half_moon_events_formatted is None
            and first_half_moon_events_formatted is None
        ):
            formatted_date_str = messages.PREDICTION_TEXT_FORMATTED_DATE.format(
                formatted_date=formatted_date
            )

            texts = [
                formatted_date_str,
                recommendations_heading,
                day_events_formatted,
                messages.USE_OTHER_FUNCTION_FOR_CORRECT_PLANNING,
            ]
        else:
            formatted_date_str = messages.PREDICTION_TEXT_FORMATTED_DATE.format(
                formatted_date=formatted_date
            )
            moon_events = messages.PREDICTION_TEXT_MOON_EVENTS.format(
                first_half_moon_events=first_half_moon_events_formatted
                or messages.NEUTRAL_BACKGROUND,
                second_half_moon_events=second_half_moon_events_formatted
                or messages.NEUTRAL_BACKGROUND,
            )

            texts = [
                formatted_date_str,
                recommendations_heading,
                day_events_formatted,
                moon_events
            ]

    formatted_text = "\n\n".join(texts)

    return formatted_text


async def get_prediction_text(date: datetime, user_id: int) -> str:
    user = crud.get_user(user_id=user_id)

    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(
        None,
        filtered_and_formatted_prediction,
        user,
        date
    )

    text = await future
    crud.add_viewed_prediction(
        user_id=user_id,
        prediction_date=date.strftime(DATE_FORMAT)
    )
    return text


async def get_formatted_selected_days(
    category: str,
    action: str,
    user: DBUser
) -> str:
    selected_aspects: list[dict] = DAY_SELECTION_DATABASE[
        category
    ][action]['aspects']

    favorably = DAY_SELECTION_DATABASE[
        category
    ][action]['favorably']

    subscription_end = datetime.strptime(
        user.subscription_end_date,
        DATETIME_FORMAT
    )

    utcnow = datetime.utcnow()
    now = utcnow + timedelta(hours=user.timezone_offset)
    start_timepoint = datetime(now.year, now.month, now.day)

    subscription_end += timedelta(hours=user.timezone_offset)
    end_timepoint = datetime(
        subscription_end.year,
        subscription_end.month,
        subscription_end.day
    )

    prediction_user = PredictionUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=PredictionLocation(
            longitude=user.birth_location.longitude,
            latitude=user.birth_location.latitude
        ),
        current_location=PredictionLocation(
            longitude=user.current_location.longitude,
            latitude=user.current_location.latitude
        ),
    )
    astro_events = await get_astro_events_from_period_with_duplicates(
        start=start_timepoint,
        finish=end_timepoint,
        user=prediction_user,
    )

    right_events = []
    for astro_event in astro_events:
        astro_event_natal_planet = SWISSEPH_PLANET_TO_UNIVERSAL_PLANET[
            astro_event.natal_planet
        ]
        astro_event_transit_planet = SWISSEPH_PLANET_TO_UNIVERSAL_PLANET[
            astro_event.transit_planet
        ]

        for aspect_group in selected_aspects:
            if (
                astro_event_natal_planet == aspect_group["natal_planet"]
                and
                astro_event_transit_planet == aspect_group["transit_planet"]
            ):
                for degree in aspect_group["degrees"]:
                    if astro_event.aspect == degree:
                        right_events.append(astro_event)

    return format_astro_events_for_day_selection(
        right_events,
        user.timezone_offset,
        favorably
    )


def format_astro_events_for_day_selection(
    events: list[AstroEvent],
    timezone_offset: int,
    favorably: bool
):
    dates: list[tuple[str, Optional[str]]] = []
    for event in events:
        local_peak_time = event.peak_at + timedelta(hours=timezone_offset)
        target_date = local_peak_time.date()

        if local_peak_time.hour < 4:
            target_date -= timedelta(days=1)

        half_day = None
        if event.transit_planet == SwissEphPlanet.MOON:
            if local_peak_time.hour >= 12:
                half_day = "(вторая половина дня)"
            else:
                half_day = "(первая половина дня)"

        date_str = target_date.strftime(UNIVERSAL_DATE_FORMAT)

        dates.append((date_str, half_day))

    return format_dates_list_for_day_selection(dates, favorably)


def format_dates_list_for_day_selection(
    dates: list[tuple[str, Optional[str]]],
    favorably: bool
) -> str:
    counter = {}
    for target_date, _ in dates:
        if target_date in counter:
            counter[target_date] += 1
        else:
            counter[target_date] = 1

    # Создаем список для результата
    result = []
    completed_dates = []

    dates = sorted(dates, key=lambda x: x[0])

    # Формируем результат в зависимости от количества повторений дат
    for target_date, suffix in dates:
        target_date_datetime = datetime.strptime(
            target_date,
            UNIVERSAL_DATE_FORMAT
        )

        date_str = format_date(
            target_date_datetime,
            format='d MMMM',
            locale='ru'
        )

        if counter[target_date] >= 2:
            if target_date not in completed_dates:
                if favorably:
                    result.append(f"🌟{date_str}")
                else:
                    result.append(f"{date_str}")
                completed_dates.append(target_date)
        elif counter[target_date] == 1:
            if suffix:
                result.append(f"{date_str} {suffix}")
            else:
                result.append(date_str)

            completed_dates.append(target_date)

    return ",\n".join(result)
