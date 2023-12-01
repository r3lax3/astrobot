from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import AdminStates


r = Router()

admin_chat_id: int = config.get(
    'admin_chat.id'
)
admin_chat_thread_cards_of_day = config.get(
    'admin_chat.threads.cards_of_day'
)

@r.callback_query(
    AdminStates.choose_action,
    F.data == bt.add_card_of_day
)
async def add_card_of_day(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    bot_message = await callback.message.answer(
        messages.send_me_card,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_card_of_day)


@r.message(
    AdminStates.get_card_of_day,
    F.photo,
    F.media_group_id.is_(None)
)
async def get_card_of_day(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    image_resend_message = await message.copy_to(
        chat_id=admin_chat_id,
        message_thread_id=admin_chat_thread_cards_of_day
    )

    database.add_card_of_day(
        message_id=image_resend_message.message_id
    )

    bot_message = await message.answer(
        messages.card_of_day_successful_saved,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])

