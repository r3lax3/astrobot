from datetime import datetime, timedelta
from typing import Dict

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User, BufferedInputFile

from src.enums import MoonSignInterpretationType, FileName
from src.routers.states import MainMenu
from src.keyboard_manager import (
    KeyboardManager, 
    bt
)
from src.database import Database
from src.astro_engine.moon import get_moon_signs_at_date
from src.image_processing import get_image_with_astrodata
from src.routers.user.moon_in_sign.text_formatting import (
    get_formatted_moon_sign_text,
)


r = Router()
FROM_BT_TO_MOON_SIGN_INTERPRETATION_TYPE: Dict[str, MoonSignInterpretationType] = {
    bt.general: MoonSignInterpretationType.GENERAL,
    bt.favorable: MoonSignInterpretationType.FAVORABLE,
    bt.unfavorable: MoonSignInterpretationType.UNFAVORABLE
}


@r.message(F.text, F.text == bt.moon_in_sign)
async def moon_sign_menu_button_handler(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await state.update_data(interpretation_type=bt.general)
    await moon_in_sign_menu(
        message,
        state,
        keyboards,
        database,
        event_from_user
    )


@r.callback_query(F.data == bt.moon_in_sign)
async def moon_in_sign_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await moon_in_sign_menu(
        callback.message,
        state,
        keyboards,
        database,
        event_from_user
    )


@r.callback_query(
    MainMenu.moon_in_sign,
    F.data.in_([bt.favorable, bt.unfavorable, bt.general])
)
async def moon_in_sign_menu_type_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await state.update_data(interpretation_type=callback.data)
    await moon_in_sign_menu(
        callback.message,
        state,
        keyboards,
        database,
        event_from_user
    )


async def moon_in_sign_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)

    data = await state.get_data()
    interpretation_type = FROM_BT_TO_MOON_SIGN_INTERPRETATION_TYPE[
        data['interpretation_type']
    ]

    timezone_offset: int = data['timezone_offset']
    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)

    moon_signs = get_moon_signs_at_date(
        date,  # %Y-%m-%d, not datetime
        timezone_offset,
        user.current_location
    )

    text = get_formatted_moon_sign_text(
        moon_signs,
        interpretation_type
    )

    photo_bytes = get_image_with_astrodata(user, database, moon_signs)
    photo = BufferedInputFile(
        file=photo_bytes,
        filename=FileName.MOON_SIGN.value
    )

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
    await state.set_state(MainMenu.moon_in_sign)

