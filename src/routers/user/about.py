from aiogram import Router, F
from aiogram.types import Message

from aiogram.fsm.context import FSMContext

from src import messages
from src.keyboard_manager import KeyboardManager, bt


r = Router()


@r.message(F.text, F.text == bt.about_bot)
async def about_bot(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.about_bot,
        reply_markup=keyboards.to_main_menu
    )
    await state.update_data(del_messages=[bot_message.message_id])

