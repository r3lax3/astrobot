from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User

from src.enums import MoonSignInterpretationType
from src.routers.states import MainMenu
from src.keyboard_manager import (
    KeyboardManager, 
    bt, 
    from_text_to_bt
)
from src.database import Database
from src.routers.user.moon_in_sign.utils import get_formatted_moon_sign_text, get_moon_signs_image
from src.astro_engine.moon import get_moon_signs_at_date


r = Router()


@r.message(F.text, F.text == bt.moon_in_sign)
async def general_moon_sign_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)
    
    timezone_offset = user.timezone_offset
    date = datetime.utcnow() + timedelta(hours=timezone_offset)

    location = user.current_location
    
    moon_signs = get_moon_signs_at_date(
        date,
        timezone_offset,
        location
    )
    text = get_formatted_moon_sign_text(
        moon_signs,
        MoonSignInterpretationType.GENERAL
    )

    photo = get_moon_signs_image(user, database, moon_signs)

    bot_message1 = await message.answer_photo(photo=photo)
    bot_message2 = await message.answer(
        text,
        reply_markup=keyboards.moon_in_sign_menu
    )
    await state.update_data(
        del_messages=[
            bot_message1.message_id,
            bot_message2.message_id
        ]
    )
    await state.set_state(MainMenu.moon_in_sign_general)


@r.callback_query(F.data == bt.moon_in_sign)
@r.callback_query(MainMenu.moon_in_sign_description, F.data == bt.back)
async def general_moon_sign_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await general_moon_sign_menu(
        callback.message,
        state,
        keyboards,
        database,
        event_from_user
    )


@r.callback_query(
    MainMenu.moon_in_sign_general,
    F.data.in_(
        [
            bt.favorable, 
            bt.unfavorable
        ]
    )
)
@r.callback_query(
    MainMenu.moon_in_sign_description,
    F.data.in_(
        [
            bt.favorable, 
            bt.unfavorable
        ]
    )
)
async def moon_in_sign_description(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)

    data = await state.get_data()

    timezone_offset: int = data['timezone_offset']
    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)

    moon_signs = get_moon_signs_at_date(
        date, 
        timezone_offset,
        user.current_location
    )

    text = get_formatted_moon_sign_text(
        moon_signs,
        MoonSignInterpretationType(from_text_to_bt[callback.data])
    )

    photo = get_moon_signs_image(user, database, moon_signs)

    bot_message1 = await callback.message.answer_photo(photo=photo)
    bot_message2 = await callback.message.answer(
        text,
        reply_markup=keyboards.moon_in_sign_menu
    )
    await state.update_data(
        del_messages=[
            bot_message1.message_id,
            bot_message2.message_id
        ]
    )
    await state.set_state(MainMenu.moon_in_sign_description)

