from datetime import datetime, timedelta
from typing import Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message, User

from src import messages
from src.astro_engine.moon import get_moon_signs_at_date
from src.database import Database
from src.enums import FileName, MoonSignInterpretationType
from src.image_processing import get_image_with_astrodata
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import MainMenu
from src.routers.user.moon_in_sign.text_formatting import (
    get_formatted_moon_sign_text
)


FROM_BT_TO_MOON_SIGN_INTERPRETATION_TYPE: Dict[str, MoonSignInterpretationType] = {
    bt.general: MoonSignInterpretationType.GENERAL,
    bt.favorable: MoonSignInterpretationType.FAVORABLE,
    bt.unfavorable: MoonSignInterpretationType.UNFAVORABLE,
}
r = Router()


@r.message(F.text, F.text == bt.moon_in_sign)
async def moon_sign_menu_button_handler(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database,
    event_from_user: User,
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
    database,
    event_from_user: User,
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
    F.data.in_([bt.favorable, bt.unfavorable, bt.blank_moon])
)
async def moon_in_sign_submenu_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database,
    event_from_user: User,
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
    database,
    event_from_user: User,
):
    user = database.get_user(event_from_user.id)

    data = await state.get_data()

    timezone_offset: int = data["timezone_offset"]
    date = (datetime.utcnow() + timedelta(hours=timezone_offset)).date()

    moon_signs = get_moon_signs_at_date(
        date,
        timezone_offset,
        user.current_location  # %Y-%m-%d, not datetime
    )
    photo_bytes = await get_image_with_astrodata(user=user, moon_signs=moon_signs)

    interpretation_type_str = data.get("interpretation_type", bt.blank_moon)
    if interpretation_type_str == bt.blank_moon:
        text = messages.BLANK_MOON_TEXT

    else:
        interpretation_type = FROM_BT_TO_MOON_SIGN_INTERPRETATION_TYPE[
            interpretation_type_str
        ]

        text = get_formatted_moon_sign_text(moon_signs, interpretation_type)

    photo = BufferedInputFile(
        file=photo_bytes,
        filename=FileName.MOON_SIGN.value
    )

    await message.answer_photo(photo=photo)
    bot_message = await message.answer(
        text,
        reply_markup=keyboards.moon_in_sign_menu
    )

    await state.update_data(delete_keyboard_message_id=bot_message.message_id)
    await state.set_state(MainMenu.moon_in_sign)
