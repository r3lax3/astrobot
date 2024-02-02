import random
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from src import config, messages
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import MainMenu

r = Router()

DATE_FORMAT: str = config.get("database.date_format")
ADMIN_CHAT_ID: int = config.get("admin_chat.id")


@r.message(F.text, F.text == bt.card_of_day)
async def card_of_day_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database,
    event_from_user: User,
    bot: Bot,
):
    user = database.get_user(event_from_user.id)

    today = datetime.utcnow() + timedelta(hours=user.timezone_offset)
    formatted_today = today.strftime(DATE_FORMAT)

    if (
        formatted_today == user.last_card_update
        and
        user.card_message_id is not None
    ):
        card_message_id = user.card_message_id
    else:
        cards = database.get_all_card_of_day()

        if len(cards) == 0:
            bot_message = await message.answer(
                messages.NO_CARDS_OF_DAY,
                reply_markup=keyboards.to_main_menu
            )
            await state.update_data(del_messages=[bot_message.message_id])
            return

        card_message_id: int = random.choice(cards)

    while True:
        try:
            card_of_day_message = await bot.copy_message(
                chat_id=event_from_user.id,           # Куда
                from_chat_id=ADMIN_CHAT_ID,           # Откуда
                message_id=card_message_id,           # Что
                caption=messages.CARD_OF_DAY,         # Текст к изображению
                reply_markup=keyboards.to_main_menu,  # Клавиатура
            )

        except TelegramBadRequest:
            cards = database.get_all_card_of_day()

            if len(cards) == 0:
                bot_message = await message.answer(
                    messages.NO_CARDS_OF_DAY,
                    reply_markup=keyboards.to_main_menu
                )
                await state.update_data(del_messages=[bot_message.message_id])
                return

            card_message_id = random.choice(cards)

        except TelegramForbiddenError:
            await state.set_state(MainMenu.end_action)
            return
        else:
            await state.update_data(
                delete_keyboard_message_id=card_of_day_message.message_id
            )
            break

    await state.set_state(MainMenu.end_action)

    # В самом конце чтобы задержку пользователь не видел
    if card_message_id != user.card_message_id:
        database.update_user_card_of_day(
            user_id=event_from_user.id,
            card_message_id=card_message_id,
            card_update_time=today.strftime(DATE_FORMAT),
        )

