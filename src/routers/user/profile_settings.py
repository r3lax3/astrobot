from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    User
)

from src.utils import get_location_by_coords
from src.routers import messages
from src.routers.states import ProfileSettings, GetBirthData
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt


from_gender_to_text = {
    'male': 'Мужчина',
    'female': 'Женщина'
}

r = Router()

@r.callback_query(
    ProfileSettings.choose_gender,
    F.data == bt.back
)
@r.callback_query(
    ProfileSettings.get_new_name,
    F.data == bt.back
)
@r.callback_query(F.data == bt.profile_settings)
async def profile_settings_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await profile_settings_menu(callback.message, state, keyboards)


@r.message(
    F.text,
    F.text == bt.profile_settings
)
async def profile_settings_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.profile_settings.format(

        ),
        reply_markup=keyboards.profile_settings
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(ProfileSettings.choose_option)


# Name


@r.callback_query(
    ProfileSettings.choose_option, 
    F.data == bt.name
)
async def change_name(    
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)
    bot_message = await callback.message.answer(
        messages.change_name.format(
            name=user.name
        ),
        reply_markup=keyboards.back
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(ProfileSettings.get_new_name)


# Gender


@r.callback_query(
    ProfileSettings.choose_option, 
    F.data == bt.gender
)
async def choose_gender(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    user = database.get_user(user_id=callback.from_user.id)
    if user.gender is not None: # Если пол не указан
        bot_message = await callback.message.answer(
            messages.choose_gender.format(
                gender=from_gender_to_text[user.gender]
            ),
            reply_markup=keyboards.choose_gender
        )
    else:
        bot_message = await callback.message.answer(
            messages.gender_not_choosen,
            reply_markup=keyboards.choose_gender
        )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(ProfileSettings.choose_gender)


@r.callback_query(
    ProfileSettings.choose_gender, 
    F.data == bt.male
)
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
    await choose_gender(
        callback,
        state,
        keyboards,
        database
    )


@r.callback_query(
    ProfileSettings.choose_gender,
    F.data == bt.female
)
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
    await choose_gender(
        callback,
        state,
        keyboards,
        database
    )


# Current Location 


@r.callback_query(
    ProfileSettings.choose_option,
    F.data == bt.change_timezone
)
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
    await state.set_state(
        ProfileSettings.get_current_location
    )


@r.message(
    ProfileSettings.get_current_location, 
    F.location
)
async def get_current_location(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    longitude = message.location.longitude
    latitude = message.location.latitude
    current_location_title = get_location_by_coords(
        longitude=longitude, latitude=latitude
    )
    bot_message = await message.answer(
        messages.get_current_location_confirm.format(
            current_location=current_location_title
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
        },
        current_location_title=current_location_title
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


@r.callback_query(
    ProfileSettings.location_confirm,
    F.data == bt.decline
)
async def get_current_location_not_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await enter_current_location(
        callback.message, state, keyboards
    )


# Redirection from ./birth.py


@r.callback_query(
    GetBirthData.confirm, 
    F.data == bt.confirm
)
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

