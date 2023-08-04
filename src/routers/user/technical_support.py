from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message
)
from aiogram.filters import Text

from src.filters import F  # IsNotSub
from src.keyboard_manager import KeyboardManager
from src.routers import messages
from src.routers.states import MainMenu


r = Router()


@r.message(Text('Техническая поддержка'))
async def technical_support_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.technical_support,
        reply_markup=keyboards.to_main_menu
    )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(MainMenu.end_action)
