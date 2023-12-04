from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User

from src import config
from src.routers.states import MainMenu
from src.keyboard_manager import (
    KeyboardManager, 
    bt, 
    from_text_to_bt
)
from src.database import Database
from src.routers.user.moon_in_sign.utils import (
    get_formatted_moon_sign_text,
    find_moon_sign_change
)


r = Router()

date_format: str = config.get('database.date_format')
time_format: str = config.get('database.time_format')


@r.message(F.text, F.text == bt.moon_in_sign)
async def general_moon_sign_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)
    
    timezone_offset: int = user.timezone_offset

    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)
    moon_signs = find_moon_sign_change(
        date,
        timezone_offset
    )
    text = get_formatted_moon_sign_text(
        moon_signs, 
        type='general'
    )

    bot_message = await message.answer(
        text,
        reply_markup=keyboards.moon_in_sign_menu
    )
    await state.update_data(
        del_messages=[bot_message.message_id],
        timezone_offset=timezone_offset
    )
    await state.set_state(MainMenu.moon_in_sign_general)


@r.callback_query(F.data == bt.moon_in_sign)
@r.callback_query(
    MainMenu.moon_in_sign_description, 
    F.data == bt.back
)
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
async def moon_in_sign_description(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    data = await state.get_data()
    timezone_offset: int = data['timezone_offset']

    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)
    moon_signs = find_moon_sign_change(date, timezone_offset)
    text = get_formatted_moon_sign_text(
        moon_signs,
        type=from_text_to_bt[callback.data]
    )
    bot_message = await callback.message.answer(
        text,
        reply_markup=keyboards.back
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(
        MainMenu.moon_in_sign_description
    )

