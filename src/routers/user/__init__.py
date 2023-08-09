from aiogram import Router
from aiogram.types import (
    Message,
    CallbackQuery,
    User
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from src.filters import F
from src.routers import messages
from src.routers.states import GetCurrentLocationFirstTime, MainMenu
from src.database import Database
from src.database.models import Location
from src.keyboard_manager import KeyboardManager

from src.routers.user.birth import enter_birth_year, r as birth_router
from src.routers.user.current_location import r as current_location_router
from src.routers.user.technical_support import r as technical_support_router
from src.routers.user.prediction import r as prediction_router


r = Router()


r.include_routers(
    birth_router,
    current_location_router,
    technical_support_router,
    prediction_router
)


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
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await user_command_start_handler(callback.message, state, keyboards, database, event_from_user)


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
    state: FSMContext
    # keyboards: KeyboardManager,
    # database: Database,
    # event_from_user: User
):
    # user = database.get_user(user_id=event_from_user.id)
    await enter_birth_year(message, state)

    # if user is None:
    #     await enter_birth_year(message, state)
    # else:
    #     await main_menu(message, state, keyboards, database)


# confirm

@r.callback_query(GetCurrentLocationFirstTime.confirm, F.data == 'Подтверждаю')
async def get_current_location_first__time_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await get_current_location_first_time_confirmed(callback.message, state, keyboards, database, event_from_user)


async def get_current_location_first_time_confirmed(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    data = await state.get_data()

    birth_datetime = data['birth_datetime']
    birth_location = data['birth_location']
    current_location = data['current_location']

    database.add_user(
        user_id=event_from_user.id,
        role='user',
        birth_datetime=birth_datetime,
        birth_location=Location(id=0, type='birth', **birth_location),
        current_location=Location(id=0, type='current', **current_location)
    )
    bot_message = await message.answer(
        messages.current_location_added
    )
    await main_menu(bot_message, state, keyboards, database)


@r.message(Command(commands=['menu']))
async def main_menu_command(
    message,
    state,
    keyboards,
    database,
    event_from_user
):
    user = database.get_user(user_id=event_from_user.id)

    if user is None:
        bot_message = await message.answer('Вы ещё не ввели данные рождения')
        await user_command_start_handler(bot_message, state)
    else:
        await main_menu(message, state, keyboards, database)


@r.message(F.text, F.text.in_(['В главное меню']))
async def main_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    await message.answer(
        messages.main_menu,
        reply_markup=keyboards.main_menu
    )
    await state.update_data(del_messages=[message.message_id])
    await state.set_state(MainMenu.choose_action)


@r.callback_query(
    F.data == 'В главное меню'
)
async def to_main_menu_button_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    await main_menu(callback.message, state, keyboards, database)


# Всякая хуйня которую я ещё не написал
@r.message(F.text, F.text.in_(['Сонник', 'Карта Дня', 'Общий прогноз', 'Луна в знаке']))
async def not_implemented_error(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    bot_message = await message.answer(
        messages.not_implemented
    )
    await main_menu(bot_message, state, keyboards, database)


# Когда на кнопку которую не нужно жмякают
@r.callback_query(F.data == 'null')
async def prediction_on_date_back():
    pass
