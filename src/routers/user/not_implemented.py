from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import messages
from src.keyboards import bt
from src.routers.user.main_menu import main_menu

r = Router()
not_implemented_list = [bt.theme]


@r.callback_query(F.data.in_(not_implemented_list))
async def not_implemented_error_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot
):
    await not_implemented_error(callback.message, state, bot)


@r.message(F.text, F.text.in_(not_implemented_list))
async def not_implemented_error(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    bot_message = await message.answer(messages.NOT_IMPLEMENTED)
    await main_menu(bot_message, state, bot)
