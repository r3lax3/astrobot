import asyncio
import logging
import time

import swisseph as swe
import datetime as dt
import csv

from datetime import datetime, timedelta
from typing import List

from aiogram import Router, F, Bot, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    User
)
from aiogram.filters import Text

from src import config
from src.models import DateModifier
from src.routers import messages
from src.routers.states import MainMenu
from src.database import Database
from src.keyboard_manager import KeyboardManager
from src.prediction_analys import (
    get_astro_events_from_period,
    User as PredictionUser,
    Location as PredictionLocation,
    AstroEvent
)


database_datetime_format = config.get('database.datetime_format')
date_format = "%Y-%m-%d"
days = config.get('constants.days')
months = config.get('constants.months')
wait_sticker = config.get('files.wait_sticker')


with open('interpretations.csv', 'r', newline="", encoding="utf-8") as file:
    interpretations = [row for row in csv.reader(file)]

interpretations_dict = {}
for intrpr in interpretations:
    interpretations_dict[
        (
            intrpr[0],
            intrpr[1],
            int(intrpr[2])
        )
    ] = intrpr

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

r = Router()


def formatted_day_events(events: List[AstroEvent]) -> str:
    intrprs = []
    for event in events:
        transit_planet = PLANET_ID_TO_NAME_RU[event.transit_planet]
        natal_planet = PLANET_ID_TO_NAME_RU[event.natal_planet]

        key = (transit_planet, natal_planet, event.aspect)
        interpretation = interpretations_dict.get(key)

        if not interpretation:
            logging.info(f'Не обнаружено интерпретации для Т. {transit_planet} - Н. {natal_planet}, {event.aspect}')
            continue
        intrprs.append(f'{interpretation[3]}')
    return '\n'.join(intrprs)


def formatted_moon_events(events: List[AstroEvent]):
    favourably = []
    unfavourably = []

    for event in events:
        transit_planet = PLANET_ID_TO_NAME_RU[event.transit_planet]
        natal_planet = PLANET_ID_TO_NAME_RU[event.natal_planet]

        key = (transit_planet, natal_planet, event.aspect)
        interpretation = interpretations_dict.get(key)

        if not interpretation:
            logging.info(f'Не обнаружено интерпретации для Т. {transit_planet} - Н. {natal_planet}, {event.aspect}')
            continue

        favourably.append(interpretation[4])
        unfavourably.append(interpretation[5])

    favourably = '\n'.join(favourably)
    unfavourably = '\n'.join(unfavourably)

    formatted_text = (
        'Благоприятно:\n'
        f'{favourably}\n\n'
        'Неблагоприятно:\n'
        f'{unfavourably}\n'
    )

    return formatted_text


def format_date_russian(date: datetime) -> str:
    # Словари с названиями дней недели и месяцев на русском языке

    # Форматирование даты
    day_name = days[date.weekday()]
    day_num = date.day
    month_name = months[date.month - 1]

    return f"{day_name}, {day_num} {month_name}"


def filtered_and_formatted_prediction(
    user: PredictionUser,
    target_date: datetime
) -> str:
    # start = time.time()
    astro_events = get_astro_events_from_period(
        start=target_date + timedelta(hours=3),  # От 3:00 утра
        finish=target_date + timedelta(hours=27),  # до 3:00 утра следующего дня,
        user=user
    )
    # p1 = time.time() - start
    # print(f"Время получения событий из движка = {p1}")

    start_of_day = target_date + timedelta(hours=6, minutes=30)
    middle_of_day = target_date + timedelta(hours=15, minutes=30)
    end_of_day = target_date + timedelta(hours=24, minutes=45)

    day_events = [
        event
        for event in astro_events
        if event.transit_planet != swe.MOON
    ]

    # Day events
    day_events_formatted = formatted_day_events(day_events) if day_events else None

    # Moon events
    first_half_moon_events = [
        event
        for event in astro_events
        if event.transit_planet == swe.MOON
        and start_of_day < event.peak_at < middle_of_day
    ]
    first_half_moon_events_formatted = (
        formatted_moon_events(first_half_moon_events) if first_half_moon_events else None
    )

    second_half_moon_events = [
        event
        for event in astro_events
        if event.transit_planet == swe.MOON
        and middle_of_day < event.peak_at < end_of_day
    ]
    second_half_moon_events_formatted = (
        formatted_moon_events(second_half_moon_events) if second_half_moon_events else None
    )

    # Date
    formatted_date = format_date_russian(date=target_date)

    if not day_events_formatted:

        if (
            second_half_moon_events_formatted is None
            and
            first_half_moon_events_formatted is None
        ):
            formatted_text = (
                f'<strong>{formatted_date}</strong>\n\n'
                'Сегодня у Вас действует общий фон. \n'
                'Чтобы правильно распланировать дела, воспользуйтесь кнопкой '
                '«Луна в знаке» или «Общий прогноз на день»'
            )
        else:
            formatted_text = (
                f'<strong>{formatted_date}</strong>\n\n'
                '<strong>*В первой половине дня*</strong>\n'
                f'{first_half_moon_events_formatted or messages.neutral_background_go_to_other_menus}\n'
                '<strong>*Во второй половине дня*</strong>\n\n'
                f'{second_half_moon_events_formatted or messages.neutral_background_go_to_other_menus}'
            )
    else:
        if (
            second_half_moon_events_formatted is None
            and
            first_half_moon_events_formatted is None
        ):
            formatted_text = (
                f'<strong>{formatted_date}</strong>\n\n'
                f'{day_events_formatted}\n\n'
                'Чтобы правильно распланировать дела в течение дня, '
                'воспользуйтесь кнопкой «Луна в знаке» или «Общий прогноз на день»'
            )
        else:
            formatted_text = (
                f'<strong>{formatted_date}</strong>\n\n'
                f'{day_events_formatted}\n\n'
                '<strong>*В первой половине дня*</strong>\n'
                f'{first_half_moon_events_formatted or messages.neutral_background}\n'
                '<strong>*Во второй половине дня*</strong>\n'
                f'{second_half_moon_events_formatted or messages.neutral_background}'
            )

    # p2 = time.time() - start - p1
    # print(f"Время форматирования текста = {p2}")
    return formatted_text


@r.message(Text('Прогнозы'))
async def get_prediction(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.prediction_descr,
        reply_markup=keyboards.predict_choose_action
    )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(MainMenu.prediction_choose_action)


@r.message(MainMenu.prediction_end, Text('Назад'))
@r.message(MainMenu.prediction_end, Text('Проверить другую дату'))
async def prediction_on_date_get_prediction_on_another_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await prediction_on_date(message, state, keyboards)


@r.message(MainMenu.prediction_choose_action, Text("Прогноз на дату"))
async def prediction_on_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await state.update_data(date=dt.date.today().strftime(date_format))
    await update_prediction_date(message, state, keyboards)


# OnDate.Back
@r.callback_query(MainMenu.prediction_choose_date, Text('Назад в меню'))
async def prediction_on_date_back(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await get_prediction(callback.message, state, keyboards)


# Confirmed
@r.callback_query(MainMenu.prediction_choose_date, Text('Подтвердить'))
async def prediction_on_date_get_prediction(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot
):
    wait_message = await callback.message.answer(messages.wait)
    sticker_message = await callback.message.answer_sticker(wait_sticker)
    data = await state.get_data()

    target_date = data['date']
    target_date = datetime.strptime(target_date, date_format)

    user = database.get_user(user_id=event_from_user.id)
    birth_location = database.get_location(user.birth_location_id)
    current_location = database.get_location(user.current_location_id)

    prediction_user = PredictionUser(
        birth_datetime=datetime.strptime(user.birth_datetime, database_datetime_format),
        birth_location=PredictionLocation(longitude=birth_location.longitude, latitude=birth_location.latitude),
        current_location=PredictionLocation(longitude=current_location.longitude, latitude=current_location.latitude)
    )

    # start = time.time()

    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(None, filtered_and_formatted_prediction, prediction_user, target_date)

    text = await future
    # p1 = time.time() - start
    # print(f'Время получения отформатированного текста предсказаний = {p1}')

    for msg in [wait_message, sticker_message]:
        try:
            await bot.delete_message(event_from_user.id, msg.message_id)
        except exceptions.TelegramBadRequest:
            continue

    bot_message = await callback.message.answer(
        text=text,
        reply_markup=keyboards.predict_completed
    )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.prediction_end)


# Updating date
@r.callback_query(MainMenu.prediction_choose_date)
async def prediction_update_date_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    date = data['date']
    date = datetime.strptime(date, date_format)
    modified_date = date + timedelta(days=DateModifier.unpack(callback.data).modifier)

    await state.update_data(date=modified_date.strftime(date_format))
    await update_prediction_date(callback.message, state, keyboards)


async def update_prediction_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    date = data['date']
    date_message = await message.answer(
        messages.prediction_at_date.format(
            date=date
        ),
        reply_markup=keyboards.predict_choose_date(date)
    )
    await state.update_data(del_messages=[date_message.message_id])
    await state.set_state(MainMenu.prediction_choose_date)

#
# @r.message(Text('тест'))
# async def test_func(message):
#     user_birth_datetime = datetime(2005, 10, 19, 9, 32)  # Дата и время рождения: 15 июня 1995 года в 12:00
#     user_birth_location = PredictionLocation(32.08452998284642, 49.42092491956057)  # Место рождения: Черкассы, Украина
#     user_current_location = PredictionLocation(30.772546984752733, 50.12033469399557)  # Текущее местоположение: Киев, Украина
#
#     test_user = PredictionUser(
#         birth_datetime=user_birth_datetime,
#         birth_location=user_birth_location,
#         current_location=user_current_location
#     )
#
#     start_date = datetime(2023, 8, 3, 3)
#     end_date = datetime(2023, 8, 4, 3)
#
#     loop = asyncio.get_running_loop()
#
#     # Получение астрологических событий и вывод результатов
#     time_list = []
#     for x in range(100):
#         print(x + 1)
#         start = time.time()
#
#         future = loop.run_in_executor(None, get_astro_events_from_period, start_date, end_date, test_user)
#
#         await future
#
#         time_list.append(time.time() - start)
#     print(f'В среднем - {sum(time_list) / len(time_list)}')
