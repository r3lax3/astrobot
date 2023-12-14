from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext

from src import messages
from src.keyboard_manager import KeyboardManager, bt
from src.routers.user.main_menu import main_menu


r = Router()
not_implemented_list = [
    bt.theme
]


# Всякая хуйня которую я ещё не написал
@r.callback_query(F.data.in_(not_implemented_list))
async def not_implemented_error_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    await not_implemented_error(
        callback.message,
        state,
        keyboards,
        bot
    )


@r.message(F.text, F.text.in_(not_implemented_list))
async def not_implemented_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    bot_message = await message.answer(
        messages.not_implemented
    )
    await main_menu(bot_message, state, keyboards, bot)

