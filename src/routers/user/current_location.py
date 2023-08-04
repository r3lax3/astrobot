from aiogram import Router
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery
)

from src.filters import F  # IsNotSub
from src.keyboard_manager import KeyboardManager
from src.routers import messages
from src.routers.states import GetBirthData, GetCurrentLocationFirstTime
from src.utils import get_location_by_coords

r = Router()


@r.callback_query(GetBirthData.confirm, Text('Подтверждаю'))
async def get_birth_data_confirm(
    callback: CallbackQuery,
    state: FSMContext,
):
    bot_message = await callback.message.answer(messages.birth_data_confirmed)
    await enter_current_location_first_time(bot_message, state)


# Current Location First Time

# location

async def enter_current_location_first_time(
    message: Message,
    state: FSMContext
):
    bot_message = await message.answer(messages.enter_current_location)
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(GetCurrentLocationFirstTime.location)


@r.message(GetCurrentLocationFirstTime.location, F.location)
async def get_current_location_first_time(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    longitude = message.location.longitude
    latitude = message.location.latitude

    bot_message = await message.answer(
        messages.get_current_location_confirm.format(
            location=get_location_by_coords(longitude=longitude, latitude=latitude)
        ),
        reply_markup=keyboards.confirm
    )

    await state.update_data(
        del_messages=[
            bot_message.message_id,
            message.message_id
        ],
        current_location={
            'latitude': latitude,
            'longitude': longitude
        }
    )
    await state.set_state(GetCurrentLocationFirstTime.confirm)
    # Подтверждение в src/routers/user/__init__.py
    # Перенёс туда чтобы избежать цикличного импорта


@r.message(GetCurrentLocationFirstTime.location)
async def get_current_location_first_time_error(
    message: Message,
    state: FSMContext,
):
    bot_message = await message.answer(messages.not_location)
    await enter_current_location_first_time(bot_message, state)


@r.callback_query(GetCurrentLocationFirstTime.confirm, Text('Нет, вернуться назад'))
async def get_current_location_first__time_not_confirmed(
    callback: CallbackQuery,
    state: FSMContext
):
    await enter_current_location_first_time(callback.message, state)
