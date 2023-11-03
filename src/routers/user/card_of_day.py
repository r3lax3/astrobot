import random

from datetime import datetime, timedelta
from typing import List

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User

from src import config
from src.routers import messages
from src.routers.states import MainMenu
from src.keyboard_manager import KeyboardManager, bt
from src.database import Database


r = Router()

card_images_folder_path = "./images/cards_of_day/"
date_format: str = config.get(
    'database.date_format'
)
admin_chat_id: int = config.get(
    'admin_chat.id'
)


@r.message(F.text, F.text == bt.card_of_day)
async def card_of_day_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot
):
    user = database.get_user(event_from_user.id)

    today = datetime.utcnow() + timedelta(hours=user.timezone_offset)
    formatted_today = today.strftime(date_format)

    cards: List[int] = None
    if (
        formatted_today == user.last_card_update 
        and
        user.card_message_id is not None
    ):
        card_message_id = user.card_message_id
    else:
        cards = database.get_all_card_of_day()
        card_message_id = random.choice(cards)
    while True:
        try:
            bot_message = await bot.copy_message(
                chat_id=event_from_user.id,   # Куда 
                from_chat_id=admin_chat_id,   # Откуда
                message_id=card_message_id,   # Что
                caption=messages.card_of_day, # Текст к изображению
                reply_markup=keyboards.back   # Клавиатура
            )
            break
        except TelegramBadRequest:
            if cards is None:
                cards = database.get_all_card_of_day()
            card_message_id = random.choice(cards)

        except TelegramForbiddenError:
            await state.set_state(MainMenu.end_action)
            return

    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(MainMenu.end_action)

    # В самом конце чтобы задержку пользователь не видел
    if card_message_id != user.card_message_id:
        database.update_user_card_of_day(
            user_id=event_from_user.id,
            card_message_id=card_message_id,
            card_update_time=today.strftime(date_format)
        )

