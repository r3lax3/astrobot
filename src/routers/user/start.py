from aiogram import Router, Bot
from aiogram.types import Message, User
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

from src import config, messages
from src.keyboard_manager import KeyboardManager
from src.filters import AdminFilter, UserFilter
from src.database import Database
from src.routers.states import MainMenu
from src.routers.user.main_menu import main_menu


r = Router()
start_video: str = config.get(
    'files.start_video'
)


# Handler for '/start' command for admin user
@r.message(CommandStart(), AdminFilter())
async def user_command_start_handler(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    await start(message, state, bot)


# Handler for '/start' command for regular users
@r.message(CommandStart(), UserFilter())
async def admin_command_start_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    database: Database,
    event_from_user: User,
    keyboards: KeyboardManager
):
    user = database.get_user(user_id=event_from_user.id)
    if user is None:
        await start(message, state, bot)
    else:
        await main_menu(message, state, keyboards)


# Function to initiate the bot interaction, sending welcome video and message
async def start(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    data = await state.get_data()

    start_message_id = data.get('start_message_id', None)
    if start_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=start_message_id
            )
        except TelegramBadRequest:
            pass
    
    start_message = await message.answer_video(
        video=start_video,
        caption=messages.start
    )
    bot_message = await message.answer(
        messages.enter_your_name
    )
    await state.update_data(
        main_menu_message_id=start_message.message_id, 
        start_message_id=start_message.message_id,
        del_messages=[bot_message.message_id]
    )
    await state.set_state(MainMenu.get_name)
