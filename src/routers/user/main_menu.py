from aiogram import Router, Bot, F
from aiogram.types import Message, User, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

from src import config
from src.routers import messages
from src.keyboard_manager import KeyboardManager, bt
from src.filters import AdminFilter, UserFilter
from src.database import Database
from src.routers.states import MainMenu, Subscription
from src.routers.user.start import start


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


# Handler for '/menu' command to display the main menu
@r.message(Command(commands=['menu']), AdminFilter())
async def main_menu_command(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot
):
    user = database.get_user(user_id=event_from_user.id)

    if user is None:
        bot_message = await message.answer(
            'Вы ещё не ввели данные рождения.'
        )
        await user_command_start_handler(bot_message, state, bot)
    else:
        await main_menu(message, state, keyboards, bot)


@r.message(
    MainMenu.predictin_every_day_choose_action, 
    F.text,
    F.text == bt.back
)
@r.message(
    F.text, 
    F.text == bt.main_menu
)
async def main_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    data = await state.get_data()
    main_menu_message_id = data.get(
        'main_menu_message_id',
        None
    )

    if main_menu_message_id is not None:
        try:
            await bot.delete_message(
                chat_id=message.chat.id, 
                message_id=main_menu_message_id
            )
        except TelegramBadRequest:
            pass

    if data['prediction_access']:
        keyboard = keyboards.main_menu
    else:
        keyboard = keyboards.main_menu_prediction_no_access

    if data['first_time']:
        main_menu_message = await message.answer(
            messages.main_menu_first_time,
            reply_markup=keyboard
        )
        await state.update_data(first_time=False)

    else:
        main_menu_message = await message.answer(
            messages.main_menu,
            reply_markup=keyboard
        )

    await state.update_data(
        del_messages=[message.message_id], 
        main_menu_message_id=main_menu_message.message_id
    )
    await state.set_state(MainMenu.choose_action)


@r.callback_query(
    F.data == bt.main_menu
)
@r.callback_query(
    Subscription.period,
    F.data == bt.back
)
async def to_main_menu_button_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    await main_menu(callback.message, state, keyboards, bot)

