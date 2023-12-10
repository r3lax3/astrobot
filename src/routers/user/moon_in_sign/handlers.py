from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User

from src import config
from src.enums import MoonSignInterpretationType, FileName
from src.routers.states import MainMenu
from src.keyboard_manager import (
    KeyboardManager, 
    bt, 
    from_text_to_bt
)
from src.database import Database
from src.routers.user.moon_in_sign.utils import get_formatted_moon_sign_text
from src.astro_engine.moon import get_moon_signs_at_date
from src.image_processing import generate_image_for_moon_signs


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
    data = await state.get_data()
    moon_sign_message_id = data.get('moon_sign_message_id', 0)

    user = database.get_user(event_from_user.id)
    
    timezone_offset: int = user.timezone_offset
    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)
    
    moon_signs = get_moon_signs_at_date(
        date,
        timezone_offset
    )
    text = get_formatted_moon_sign_text(
        moon_signs,
        MoonSignInterpretationType.GENERAL
    )

    if message.message_id == moon_sign_message_id:
        await message.edit_text(text)
        await message.edit_reply_markup(reply_markup=keyboards.moon_in_sign_menu)
    else:
        bot_message = await message.answer_photo(
            photo=BufferedInputFile(
                file=generate_image_for_moon_signs(
                    date=date.strftime(date_format),
                    moon_phase=...,
                    **moon_signs
                ),
                filename=FileName.moon_sign.value
            ),
            caption=text,
            reply_markup=keyboards.moon_in_sign_menu
        )
        await state.update_data(
            del_messages=[bot_message.message_id]
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
async def moon_in_sign_description(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    data = await state.get_data()
    timezone_offset: int = data['timezone_offset']

    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)
    moon_signs = get_moon_signs_at_date(date, timezone_offset)
    text = get_formatted_moon_sign_text(
        moon_signs,
        MoonSignInterpretationType(from_text_to_bt[callback.data])
    )

    await callback.message.edit_text(text)
    await callback.message.edit_reply_markup(reply_markup=keyboards.back)
    
    await state.set_state(MainMenu.moon_in_sign_description)

