from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src import messages
from src.routers.states import MainMenu
from src.keyboard_manager import KeyboardManager, bt

r = Router()


@r.message(F.text == bt.tech_support)
async def technical_support_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.technical_support,
        reply_markup=keyboards.to_main_menu
    )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.end_action)

