from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src import messages
from src.keyboards import keyboards, bt
from src.routers.states import MainMenu

r = Router()


@r.message(F.text == bt.support)
async def support_menu(
    message: Message,
    state: FSMContext
):
    bot_message = await message.answer(
        messages.SUPPORT,
        reply_markup=keyboards.to_main_menu()
    )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.end_action)
