from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery
)

from src.utils import get_location_by_coords
from src.routers import messages
from src.routers.states import ProfileSettings, GetBirthData, GetCurrentLocation
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt


r = Router()


@r.message(F.text, F.text == bt.profile_settings)
async def profile_settings_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.profile_settings,
        reply_markup=keyboards.profile_settings
    )
    await state.update_data(del_messages=[bot_message.message_id])


# Gender


@r.callback_query(ProfileSettings.choose_option, F.data == bt.gender)
async def choose_gender(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.choose_gender,
        reply_markup=keyboards.choose_gender
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(ProfileSettings.choose_gender)


@r.callback_query(ProfileSettings.choose_gender, F.data == bt.male)
async def gender_is_male(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    database.change_user_gender(
        gender='male', 
        user_id=callback.from_user.id
    )
    await choose_gender(callback, state, keyboards)


@r.callback_query(ProfileSettings.choose_gender, F.data == bt.female)
async def gender_is_female(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    database.change_user_gender(
        gender='female', 
        user_id=callback.from_user.id
    )
    await choose_gender(callback, state, keyboards)


# Current Location 


@r.callback_query(ProfileSettings.choose_option, F.data == bt.change_timezone)
async def enter_current_location(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()
    first_time = data['first_time']
    if not first_time:
        bot_message = await callback.message.answer(
            messages.enter_current_location,
            reply_markup=keyboards.to_main_menu
        )
    else:
        bot_message = await callback.message.answer(
            messages.enter_current_location
        )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(GetCurrentLocation.location)


@r.message(ProfileSettings.get_current_location, F.location)
async def get_current_location(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    longitude = message.location.longitude
    latitude = message.location.latitude

    bot_message = await message.answer(
        messages.get_current_location_confirm.format(
            location=get_location_by_coords(
                longitude=longitude, latitude=latitude
            )
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
    await state.set_state(ProfileSettings.location_confirm)


@r.message(ProfileSettings.get_current_location)
async def get_current_location_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(messages.not_location)
    await enter_current_location(bot_message, state, keyboards)


@r.callback_query(ProfileSettings.location_confirm, F.data == bt.decline)
async def get_current_location_not_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_current_location(
        callback.message, state, keyboards
    )


# Redirection from ./birth.py


@r.callback_query(GetBirthData.confirm, F.data == bt.confirm)
async def get_birth_data_confirm(
    callback: CallbackQuery,
    state: FSMContext,
):
    bot_message = await callback.message.answer(
        messages.birth_data_confirmed
    )
    await state.update_data(
        del_messages=[bot_message.message_id],
        first_time=True
    )
    await state.set_state(ProfileSettings.get_current_location)

