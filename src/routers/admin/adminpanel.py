from typing import List

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.keyboards import keyboards, bt
from src.routers.states import AdminStates

r = Router()

ADMINS: List[int] = config.get("admins.ids")


@r.callback_query(AdminStates.get_general_prediction_date, F.data == bt.back)
@r.callback_query(F.from_user.id.in_(ADMINS), F.data == bt.back_to_adminpanel)
async def adminpane_callback_query_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    await adminpanel(callback.message, state)


@r.message(Command(commands=["admin"]), F.from_user.id.in_(ADMINS))
async def adminpanel(message: Message, state: FSMContext):
    bot_message = await message.answer(
        messages.ADMIN_MENU,
        reply_markup=keyboards.adminpanel()
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.choose_action)
