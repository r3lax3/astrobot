from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src import messages
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import MainMenu

r = Router()


@r.message(F.text == bt.support)
async def support_menu(
    message: Message, state: FSMContext, keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.support, 
        reply_markup=keyboards.to_main_menu
    )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.end_action)
