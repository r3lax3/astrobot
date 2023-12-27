import asyncio
import logging

import swisseph as swe
import csv

from datetime import datetime, timedelta
from typing import List
from src import config, messages
from src.database import Database
from src.astro_engine.predictions import get_astro_events_from_period
from src.astro_engine.models import (
    User as PredictionUser,
    Location as PredictionLocation,
    AstroEvent
)
from src.routers.user.prediction.models import Interpretation


def get_interpretations_dict():
    with open(
        file='interpretations.csv', 
        mode='r', 
        newline="", 
        encoding="utf-8"
    ) as file:
        interpretations = [
            row 
            for row in csv.reader(file)
        ]

        interpretations_dict = {}
        for interpretation in interpretations:
            # key is tuple(transit_planet, natal_planet, event_aspect)
            interpretation[2] = int(interpretation[2])
            key = tuple(interpretation[:3])

            interpretations_dict[key] = Interpretation(*interpretation)

    return interpretations_dict


DATETIME_FORMAT: str = config.get('database.datetime_format')
DATE_FORMAT: str = config.get('database.date_format')
TIME_FORMAT: str = config.get('database.time_format')

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

PLANET_ID_TO_NAME_RU = {
    0: "Солнце",
    1: "Луна",
    2: "Меркурий",
    3: "Венера",
    4: "Марс",
    5: "Юпитер",
    6: "Сатурн",
    7: "Уран",
    8: "Нептун",
    9: "Плутон"
}


def formatted_general_events(events: List[AstroEvent]) -> str:
    interpretations = []
    for event in events:
        transit_planet = PLANET_ID_TO_NAME_RU[event.transit_planet]
        natal_planet = PLANET_ID_TO_NAME_RU[event.natal_planet]
        aspect=event.aspect

        interpretation = interpretations_dict.get(
            (transit_planet, natal_planet, event.aspect),
            None
        )

        if interpretation is None:
            interpretation = interpretations_dict.get(
                (natal_planet, transit_planet, event.aspect),
                None
            )

        if not interpretation:
            logging.info(
                messages.no_interpretation.format(
                    transit_planet=transit_planet,
                    natal_planet=natal_planet,
                    aspect=aspect
                )
            )
            continue
        interpretations.append(
            f'💫{interpretation.general}'
        )
    return '\n\n'.join(interpretations)


def formatted_moon_events(events: List[AstroEvent]):
    favorably = []
    unfavorably = []

    for event in events:
        transit_planet = PLANET_ID_TO_NAME_RU[event.transit_planet]
        natal_planet = PLANET_ID_TO_NAME_RU[event.natal_planet]
        aspect = event.aspect

        interpretation = interpretations_dict.get(
            (transit_planet, natal_planet, event.aspect),
            None
        )

        if interpretation is None:
            interpretation = interpretations_dict.get(
                (natal_planet, transit_planet, event.aspect),
                None
            )

        if not interpretation:
            logging.info(
                messages.no_interpretation.format(
                    transit_planet=transit_planet,
                    natal_planet=natal_planet,
                    aspect=aspect
                )
            )
            continue

        favorably.append(interpretation.favorably.strip())
        unfavorably.append(interpretation.unfavorably.strip())

    favorably = '\n'.join(favorably)
    unfavorably = '\n'.join(unfavorably)

    formatted_text = messages.favorable_and_unfavorable.format(
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


def filtered_and_formatted_prediction(
    user: PredictionUser,
    target_date: datetime
) -> str:
    astro_events = get_astro_events_from_period(
        start=target_date + timedelta(hours=3),  # От 3:00 утра
        finish=target_date + timedelta(hours=27),  # до 3:00 утра следующего дня,
        user=user
    )

    start_of_day = target_date + timedelta(hours=6, minutes=30)
    middle_of_day = target_date + timedelta(hours=15, minutes=30)
    end_of_day = target_date + timedelta(hours=24, minutes=45)

    day_events = [
        event
        for event in astro_events
        if event.transit_planet != swe.MOON
    ]

    # Day events
    day_events_formatted = (
        formatted_general_events(day_events)
        if day_events
        else None
    )

    # Moon events
    first_half_moon_events = [
        event
        for event in astro_events
        if event.peak_at
        and start_of_day < event.peak_at < middle_of_day
    ]
    first_half_moon_events_formatted = (
        formatted_moon_events(first_half_moon_events) 
        if first_half_moon_events
        else None
    )

    second_half_moon_events = [
        event
        for event in astro_events
        if event.peak_at
        and middle_of_day < event.peak_at < end_of_day
    ]
    second_half_moon_events_formatted = (
        formatted_moon_events(second_half_moon_events) 
        if second_half_moon_events 
        else None
    )

    # Date
    formatted_date = format_date_russian(date=target_date)
    texts = []

    if not day_events_formatted:

        if (
            second_half_moon_events_formatted is None
            and
            first_half_moon_events_formatted is None
        ):
            formatted_date_str = messages.prediction_text_formatted_date.format(
                formatted_date=formatted_date
            )

            texts = [
                formatted_date_str, 
                messages.prediction_text_neutral_background_today,
                messages.use_other_function_for_correct_planning, 
            ]
        else:
            formatted_date_str = messages.prediction_text_formatted_date.format(
                formatted_date=formatted_date
            )
            default_moon_sign_text = (
                messages.prediction_text_neutral_background + '\n\n' + 
                messages.use_other_function_for_correct_planning
            )
            moon_events = messages.prediction_text_moon_events.format(
                first_half_moon_events=first_half_moon_events_formatted or default_moon_sign_text,
                second_half_moon_events=second_half_moon_events_formatted or default_moon_sign_text
            )

            texts = [
                formatted_date_str, 
                moon_events
            ]
    else:
        if (
            second_half_moon_events_formatted is None
            and
            first_half_moon_events_formatted is None
        ):
            formatted_date_str = messages.prediction_text_formatted_date.format(
                formatted_date=formatted_date
            )

            texts = [
                formatted_date_str, 
                day_events_formatted, 
                messages.use_other_function_for_correct_planning
            ]
        else:
            formatted_date_str = messages.prediction_text_formatted_date.format(
                formatted_date=formatted_date
            )
            moon_events = messages.prediction_text_moon_events.format(
                first_half_moon_events=first_half_moon_events_formatted or messages.neutral_background,
                second_half_moon_events=second_half_moon_events_formatted or messages.neutral_background
            )

            texts = [
                formatted_date_str, 
                day_events_formatted,
                moon_events
            ]

    formatted_text = '\n\n'.join(texts)

    return formatted_text

async def get_prediction_text(
    target_date: datetime,
    database: Database,
    user_id: int
) -> str:
    user = database.get_user(user_id=user_id)
    birth_location = database.get_location(user.birth_location_id)
    current_location = database.get_location(user.current_location_id)

    prediction_user = PredictionUser(
        birth_datetime=datetime.strptime(
            user.birth_datetime,
            DATETIME_FORMAT
        ),
        birth_location=PredictionLocation(
            longitude=birth_location.longitude,
            latitude=birth_location.latitude
        ),
        current_location=PredictionLocation(
            longitude=current_location.longitude,
            latitude=current_location.latitude
        )
    )

    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(
        None, 
        filtered_and_formatted_prediction, 
        prediction_user, 
        target_date
    )

    text = await future
    database.add_viewed_prediction(
        user_id=user_id,
        prediction_date=target_date.strftime(DATE_FORMAT)
    )
    return text

