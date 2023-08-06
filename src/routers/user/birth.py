import calendar
import logging

from datetime import datetime

from aiogram import Router
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InputMediaPhoto
)

from src import config
from src.filters import F  # IsNotSub
from src.keyboard_manager import KeyboardManager
from src.routers import messages
from src.routers.states import GetBirthData
from src.utils import is_int, get_location_by_coords


r = Router()

regexp_time = r"(?:[01]?\d|2[0-3]):[0-5]\d"
database_datetime_format = config.get('database.datetime_format')
guide_send_geopos_images_file_id = config.get('files.how_to_send_geopos_screenshots')


# Год
@r.message(GetBirthData.year, F.text)
async def get_birth_year_message_handler(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    if not is_int(message.text) or not (  # Если он ввёл не число, а какую-то хуйню
        1900 < int(message.text) < datetime.now().year  # Если человеку больше 150-ти или он путешественник из будущего
    ):
        await get_birth_year_error(message, state)
    else:
        await state.update_data(year=int(message.text))
        await enter_birth_month(message, state, keyboards)


@r.message(GetBirthData.year)
async def get_birth_year_error(
    message: Message,
    state: FSMContext,
):
    bot_message = await message.answer(messages.not_year)
    await enter_birth_year(bot_message, state)


async def enter_birth_year(
    message: Message,
    state: FSMContext,
):
    bot_message = await message.answer(
        messages.enter_birth_year
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(GetBirthData.year)


# Месяц

@r.callback_query(GetBirthData.month, F.data == 'Назад')
async def get_birth_month_back(
    callback: CallbackQuery,
    state: FSMContext,
):
    await enter_birth_year(callback.message, state)


@r.callback_query(GetBirthData.month)
async def get_birth_month(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await state.update_data(month=int(callback.data))
    logging.info('введи день')
    await enter_birth_day(callback.message, state, keyboards)


async def enter_birth_month(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.enter_birth_month,
        reply_markup=keyboards.enter_birth_month
    )
    await state.update_data(
        del_messages=[bot_message.message_id, message.message_id]
    )
    await state.set_state(GetBirthData.month)


# День

@r.callback_query(GetBirthData.day, Text('Назад'))
async def get_birth_day_back(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_birth_month(callback.message, state, keyboards)


@r.message(GetBirthData.day, F.text)
async def get_birth_day(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    if not is_int(message.text):
        bot_message = await message.answer(messages.not_day)
        await state.update_data(del_messages=[bot_message.message_id, message.message_id])
        return

    data = await state.get_data()

    year = data['year']
    month = data['month']

    # От нуля до максимальной длины текущего месяца в днях.
    # calendar.monthrange(year=year, month=month)[1] возвращает числом кол-во дней в месяце.
    if 0 < int(message.text) <= calendar.monthrange(year=year, month=month)[1]:
        await state.update_data(day=int(message.text))
        await enter_birth_time(message, state, keyboards)
    else:
        bot_message = await message.answer(messages.not_day)
        await state.update_data(del_messages=[bot_message.message_id, message.message_id])


async def enter_birth_day(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.enter_birth_day,
        reply_markup=keyboards.back
    )
    await state.update_data(
        del_messages=[bot_message.message_id, message.message_id]
    )
    await state.set_state(GetBirthData.day)


# Время

@r.callback_query(GetBirthData.time, Text('Назад'))
async def get_birth_time_back(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_birth_day(callback.message, state, keyboards)


@r.message(GetBirthData.time, F.text, F.text.regexp(regexp_time))
async def get_birth_time(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    hour, minute = map(int, message.text.split(':'))  # из "09:23" в hour=9, minute=23

    await state.update_data(hour=hour, minute=minute)
    await enter_birth_geopos(message, state, keyboards)


@r.callback_query(GetBirthData.time)
async def get_birth_time(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    hour, minute = map(int, callback.data.split(':'))  # из "09:23" в hour=9, minute=23

    await state.update_data(hour=hour, minute=minute)
    await enter_birth_geopos(callback.message, state, keyboards)


@r.message(GetBirthData.time)
async def get_birth_time_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    bot_message = await message.answer(
        messages.not_time
    )
    await enter_birth_time(bot_message, state, keyboards)


async def enter_birth_time(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.enter_birth_time,
        reply_markup=keyboards.choose_time
    )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(GetBirthData.time)


# Местоположение рождения

async def enter_birth_geopos(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    images = await message.answer_media_group(
        [
            InputMediaPhoto(
                media=guide_send_geopos_images_file_id[0]
            ),
            InputMediaPhoto(
                media=guide_send_geopos_images_file_id[1]
            ),
            InputMediaPhoto(
                media=guide_send_geopos_images_file_id[2]
            )
        ]
    )
    bot_message = await message.answer(
        messages.enter_birth_geopos,
        reply_markup=keyboards.back
    )

    await state.update_data(
        del_messages=[
            *[msg.message_id for msg in images],
            message.message_id,
            bot_message.message_id
        ]
    )
    await state.set_state(GetBirthData.location)


@r.callback_query(GetBirthData.location, Text('Назад'))
async def get_birth_geopos_back(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_birth_time(callback.message, state, keyboards)


@r.message(GetBirthData.location, F.location)
async def get_birth_geopos(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    longitude = message.location.longitude
    latitude = message.location.latitude

    await state.update_data(
        longitude=longitude,
        latitude=latitude
    )

    await enter_birth_data_confirm(message, state, keyboards)


@r.message(GetBirthData.location)
async def get_birth_geopos_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.not_location
    )
    await enter_birth_geopos(bot_message, state, keyboards)


# Confirm

@r.callback_query(GetBirthData.confirm, Text('Нет, вернуться назад'))
async def birth_data_not_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_birth_geopos(callback.message, state, keyboards)


async def enter_birth_data_confirm(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    year = data['year']
    month = data['month']
    day = data['day']

    hour = data['hour']
    minute = data['minute']

    longitude = data['longitude']
    latitude = data['latitude']

    birth_datetime = datetime(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute
    ).strftime(database_datetime_format)

    bot_message = await message.answer(
        messages.birth_data_confirm.format(
            birth_datetime=birth_datetime,
            location=get_location_by_coords(longitude, latitude)
        ),
        reply_markup=keyboards.confirm
    )
    await state.update_data(
        del_messages=[bot_message.message_id, message.message_id],
        birth_datetime=birth_datetime,
        birth_location={
            'latitude': latitude,
            'longitude': longitude
        }
    )
    await state.set_state(GetBirthData.confirm)
    # Подтверждение перекидывает в логику, которая прописана в src/routers/now_location. Смотри начало файла
