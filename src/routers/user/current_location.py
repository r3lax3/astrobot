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
from src.routers.states import GetBirthData, GetCurrentLocation
from src.utils import get_location_by_coords


r = Router()


@r.callback_query(GetBirthData.confirm, Text('Подтверждаю ☑'))
async def get_birth_data_confirm(
    callback: CallbackQuery,
    state: FSMContext,
):
    bot_message = await callback.message.answer(messages.birth_data_confirmed)
    await state.update_data(del_messages=[bot_message.message_id], first_time=True)
    await state.set_state(GetCurrentLocation.location)


# Current Location 

# location

@r.message(F.text, F.text == '✈️Смена часового пояса')
async def enter_current_location(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    date = await state.get_data()
    first_time = date['first_time']
    if not first_time:
        bot_message = await message.answer(
            messages.enter_current_location,
            reply_markup=keyboards.to_main_menu
        )
    else:
        bot_message = await message.answer(
            messages.enter_current_location
        )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(GetCurrentLocation.location)


@r.message(GetCurrentLocation.location, F.location)
async def get_current_location(
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
    await state.set_state(GetCurrentLocation.confirm)
    # Подтверждение в src/routers/user/__init__.py
    # Перенёс туда чтобы избежать цикличного импорта


@r.message(GetCurrentLocation.location)
async def get_current_location_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(messages.not_location)
    await enter_current_location(bot_message, state, keyboards)


@r.callback_query(GetCurrentLocation.confirm, Text('Нет, вернуться назад ❎'))
async def get_current_location_not_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_current_location(callback.message, state, keyboards)

