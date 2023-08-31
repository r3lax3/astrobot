import calendar
from dataclasses import replace
import logging

from datetime import datetime

from aiogram import Router, F
from aiogram.client import bot
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InputMediaPhoto
)
from magic_filter.operations import call

from src import config
from src.utils import is_int, get_location_by_coords
from src.routers import messages
from src.routers.states import GetBirthData
from src.filters import IsDate
from src.keyboard_manager import KeyboardManager

r = Router()

regexp_time = r"(?:[01]?\d|2[0-3]):[0-5]\d"
database_datetime_format = config.get('database.datetime_format')
date_format = config.get('database.date_format')
guide_send_geopos_images_file_id = config.get('files.how_to_send_geopos_screenshots')


@r.callback_query(F.data == 'Ввести данные рождения')
async def enter_birth_date_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    await enter_birth_date(callback.message, state)

async def enter_birth_date(
    message: Message,
    state: FSMContext,
):
    bot_message = await message.answer(
        messages.enter_birth_date
    )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(GetBirthData.date)


@r.message(GetBirthData.date, IsDate())
async def get_birth_date_handler(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await state.update_data(date=message.text)
    await get_birth_date(message, state, keyboards)


async def get_birth_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()
    date_str = data['date']

    birth_date = datetime.strptime(date_str, date_format)
    now = datetime.now()

    delta = now - birth_date
    delta_years = round(delta.days / 365)  # need in validation

    if 0 < delta_years < 100:
        await enter_birth_time(message, state, keyboards)
    else:
        await get_birth_date_error(message, state)


@r.message(GetBirthData.date)
async def get_birth_date_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        '*Текст ошибки, которая возникает когда человек или "родился в будущем" или когда ему больше 100 лет*'
    )
    await enter_birth_date(bot_message, state)


# Время
@r.callback_query(GetBirthData.time, F.data == '🔙 Назад')
async def get_birth_time_back(
    callback: CallbackQuery,
    state: FSMContext
):
    await enter_birth_date(callback.message, state)


@r.message(GetBirthData.time, F.text, F.text.regexp(regexp_time))
async def get_birth_time(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    hour, minute = map(int, message.text.split(':'))  # из "09:23" в (9, 23), а дальше просто распаковка

    await state.update_data(hour=hour, minute=minute, time=message.text)
    await enter_birth_geopos(message, state, keyboards)


@r.callback_query(GetBirthData.time, F.data.regexp(regexp_time))
async def get_birth_time_from_button(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    hour, minute = map(int, callback.data.split(':')) 

    await state.update_data(hour=hour, minute=minute, time=callback.data)
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
    data = await state.get_data()
    date_str = data['date']

    current_data_message = await message.answer(
        messages.current_birth_data.format(
            date=date_str,
            time='___',
            birth_location='___'
        )
    )
    enter_time_message = await message.answer(
        messages.enter_birth_time,
        reply_markup=keyboards.choose_time
    )
    
    await state.update_data(
        del_messages=[current_data_message.message_id, enter_time_message.message_id, message.message_id],
    )
    await state.set_state(GetBirthData.time)


# Местоположение рождения

async def enter_birth_geopos(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()
    date_str = data['date']
    time_str = data['time']

    current_data_message = await message.answer(
        messages.current_birth_data.format(
            date=date_str,
            time=time_str,
            birth_location='___'
        )
    )
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
            bot_message.message_id,
            current_data_message.message_id,
            message.message_id
        ]
    )
    await state.set_state(GetBirthData.location)


@r.callback_query(GetBirthData.location, F.data == '🔙 Назад')
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

@r.callback_query(GetBirthData.confirm, F.data == 'Нет, вернуться назад ❎')
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
    date_str = data['date']
    time_str = data['time']


    year, month, day = map(int, date_str.split('-'))

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

    birth_data_confirm_message = await message.answer(
        messages.birth_data_confirm.format(
            date=date_str,
            time=time_str,
            birth_location=get_location_by_coords(longitude, latitude)
        ),
        reply_markup=keyboards.confirm
    )

    await state.update_data(
        del_messages=[birth_data_confirm_message.message_id, message.message_id],
        birth_datetime=birth_datetime,
        birth_location={
            'latitude': latitude,
            'longitude': longitude
        }
    )
    await state.set_state(GetBirthData.confirm)
    # Подтверждение перекидывает в логику, которая прописана в src/routers/now_location. Смотри начало файла
