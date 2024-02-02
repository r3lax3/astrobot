from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src import messages
from src.keyboard_manager import KeyboardManager, bt

r = Router()


@r.message(F.text, F.text == bt.about_bot)
async def about_bot(message: Message, state: FSMContext, keyboards: KeyboardManager):
    bot_message = await message.answer(
        messages.ABOUT_BOT, reply_markup=keyboards.to_main_menu
    )
    await state.update_data(del_messages=[bot_message.message_id])
