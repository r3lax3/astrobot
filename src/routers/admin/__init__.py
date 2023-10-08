from typing import List

from aiogram import Router, F
from aiogram.filters.callback_data import CallbackQueryFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, CallbackQuery
from aiogram.filters import Command

from src import config
from src.routers import messages
from src.routers.states import AdminStates
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt


r = Router()
admins: List[int] = config.get('admins.ids')


@r.message(Command(commands=['/admin']), F.from_user.id.in_(admins))
async def adminpanel(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.admin_menu,
        reply_markup=keyboards.adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])


# @r.callback_query(AdminStates.choose_action, F.data == bt.general_predictions_add)
# async def general_predictions_add_menu(
#     callback: CallbackQuery,
#     state: FSMContext,
#     keyboards: KeyboardManager
# ):
#     
#
#
# @r.callback_query(AdminStates.choose_action, F.data == bt.user_settings)
#
