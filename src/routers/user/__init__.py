from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    User
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from src import config

from src.routers import messages
from src.routers.states import GetCurrentLocation, MainMenu
from src.routers.user.birth import r as birth_router
from src.routers.user.current_location import r as current_location_router
from src.routers.user.technical_support import r as technical_support_router
from src.routers.user.prediction import r as prediction_router

from src.database import Database
from src.database.models import Location

from src.keyboard_manager import KeyboardManager

r = Router()
r.include_routers(
    birth_router,
    current_location_router,
    technical_support_router,
    prediction_router
)

start_video = config.get('files.start_video')


# @r.callback_query(Text('Попробовать зайти ещё раз'), IsNotSub())
# async def try_start_again_for_unsub(
#     callback: CallbackQuery,
#     state: FSMContext,
#     keyboards: KeyboardManager,
#     database: Database,
#     event_from_user: User
# ):
#     await user_command_start_handler_for_unsub(callback.message, state, keyboards, database, event_from_user)


@r.callback_query(F.data == 'Попробовать зайти ещё раз')
async def try_start_again_for_sub(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await user_command_start_handler(callback.message, state, keyboards)


# @r.message(CommandStart(), IsNotSub())
# async def user_command_start_handler_for_unsub(
#     message: Message,
#     state: FSMContext,
#     keyboards: KeyboardManager,
#     database: Database,
#     event_from_user: User
# ):
#     ...
#
#     check_user_in_database(event_from_user, database)


@r.message(CommandStart())
async def user_command_start_handler(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    # database: Database,
    # event_from_user: User
):
    # user = database.get_user(user_id=event_from_user.id)

    # if user is None:
        await start(message, state, keyboards)
    # else:
    #     await main_menu(message, state, keyboards)


async def start(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    start_message = await message.answer_video(
        video=start_video,
        caption=messages.start,
        reply_markup=keyboards.start
    )
    await state.update_data(del_messages=[start_message.message_id])


# Confirm
@r.callback_query(GetCurrentLocation.confirm, F.data == 'Подтверждаю ☑')
async def get_current_location_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot
):
    data = await state.get_data()

    current_location = data['current_location']

    if data['first_time']:
        birth_datetime = data['birth_datetime']
        birth_location = data['birth_location']

        database.add_user(
            user_id=event_from_user.id,
            role='user',
            birth_datetime=birth_datetime,
            birth_location=Location(id=0, type='birth', **birth_location),
            current_location=Location(id=0, type='current', **current_location)
        )
        bot_message = await callback.message.answer(
            messages.current_location_added
        )
    else:
        database.update_user_current_location(event_from_user.id, Location(id=0, type='current', **current_location))
        bot_message = await callback.message.answer(
            messages.current_location_updated
        )       

    await main_menu(bot_message, state, keyboards, bot)


@r.message(Command(commands=['menu']))
async def main_menu_command(
    message,
    state,
    keyboards,
    database,
    event_from_user,
    bot: Bot
):
    user = database.get_user(user_id=event_from_user.id)

    if user is None:
        bot_message = await message.answer('Вы ещё не ввели данные рождения')
        await user_command_start_handler(bot_message, state)
    else:
        await main_menu(message, state, keyboards, bot)


@r.message(F.text, F.text.in_(['В главное меню']))
async def main_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    bot: Bot
):
    data = await state.get_data()

    main_menu_message_id = data.get('main_menu_message_id', None)
    if main_menu_message_id is not None:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=main_menu_message_id)
        except:
            pass

    if data['first_time']:
        main_menu_message = await message.answer(
            messages.main_menu_first_time,
            reply_markup=keyboards.main_menu
        )
        await state.update_data(first_time=False)
    else:
        main_menu_message = await message.answer(
            messages.main_menu,
            reply_markup=keyboards.main_menu
        )
    await state.update_data(del_messages=[message.message_id], main_menu_message_id=main_menu_message.message_id)
    await state.set_state(MainMenu.choose_action)


@r.callback_query(
    F.data == 'В главное меню'
)
async def to_main_menu_button_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    bot: Bot,
):
    await main_menu(callback.message, state, keyboards, bot)




# Всякая хуйня которую я ещё не написал
@r.message(F.text, F.text.in_(['💫 Сны', 'Карта Дня', '🌒 Общие прогнозы', '🌗 Луна в знаке']))
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


# Когда на кнопку которую не нужно жмякают
@r.callback_query(F.data == 'null')
async def prediction_on_date_back():
    pass
