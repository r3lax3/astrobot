from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import config, messages
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import AdminStates

r = Router()

ADMIN_CHAT_ID: int = config.get("admin_chat.id")
ADMIN_CHAT_THREAD_CARDS_OF_DAY = config.get("admin_chat.threads.cards_of_day")


@r.callback_query(AdminStates.choose_action, F.data == bt.add_card_of_day)
async def add_card_of_day(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    bot_message = await callback.message.answer(
        messages.send_me_card, reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_card_of_day)


@r.message(AdminStates.get_card_of_day, F.photo)
async def get_card_of_day(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    bot: Bot,
    event_from_user: User,
):
    data = await state.get_data()

    album = data.get("album", None)
    if album:
        for photo_message_id in album:
            await add_card_of_day(bot, photo_message_id, event_from_user, database)

    else:
        photo_message_id = message.message_id
        await add_card_of_day(bot, photo_message_id, event_from_user, database)

    bot_message = await message.answer(
        messages.card_of_day_successful_saved, reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])


async def add_card_of_day(
    bot: Bot, photo_message_id: int, event_from_user: User, database: Database
):
    image_resend_message = await bot.copy_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=event_from_user.id,
        message_thread_id=ADMIN_CHAT_THREAD_CARDS_OF_DAY,
        message_id=photo_message_id,
    )

    database.add_card_of_day(message_id=image_resend_message.message_id)
