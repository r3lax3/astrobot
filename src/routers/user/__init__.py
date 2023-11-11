from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    User
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from src import config
from src.scheduler import EveryDayPredictionScheduler
from src.routers import messages
from src.routers.states import ProfileSettings, MainMenu, Subscription
from src.routers.user.birth import r as birth_router
from src.routers.user.technical_support import r as technical_support_router
from src.routers.user.prediction import r as prediction_router
from src.routers.user.subsription import r as subsription_router
from src.routers.user.card_of_day import r as card_of_day_router
from src.routers.user.compatibility import r as compatibility_router
from src.routers.user.profile_settings import r as profile_settings_router
from src.routers.user.general_predictions import r as general_predictions_router
from src.routers.user.moon_in_sign import r as moon_in_sign_router

from src.database import Database
from src.database.models import Location, User as DBUser

from src.keyboard_manager import KeyboardManager, bt
from src.utils import get_location_by_coords, get_timezone_offset


r = Router()
r.include_routers(
    birth_router,
    profile_settings_router,
    technical_support_router,
    prediction_router,
    subsription_router,
    compatibility_router,
    general_predictions_router,
    card_of_day_router,
    moon_in_sign_router
)

start_video: str = config.get(
    'files.start_video'
)
database_datetime_format: str = config.get(
    'database.datetime_format'
)
not_implemented_list = [
    bt.dreams, 
    bt.theme
]
subscription_test_period_in_days: int = config.get(
    'subscription.test_period_in_days'
)



@r.callback_query(
    F.data == 'Попробовать зайти ещё раз'
)
async def try_start_again_for_sub(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await user_command_start_handler(
        callback.message,
        state, 
        keyboards
    )



@r.message(CommandStart())
async def user_command_start_handler(
    message: Message,
    state: FSMContext,
    bot: Bot
    # database: Database,
    # event_from_user: User
):
    # user = database.get_user(user_id=event_from_user.id)

    # if user is None:
        await start(message, state, bot)
    # else:
    #     await main_menu(message, state, keyboards)


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


# Confirm
@r.callback_query(
    ProfileSettings.location_confirm, 
    F.data == bt.confirm
)
async def get_current_location_confirmed(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
    bot: Bot,
    scheduler: EveryDayPredictionScheduler
):
    data = await state.get_data()
    
    name = data['name']
    current_location = data['current_location']
    current_location_title = data['current_location_title']

    if data['first_time']:
        birth_datetime = data['birth_datetime']
        birth_location = data['birth_location']
        birth_location_title = data['birth_location_title']
        
        now = datetime.utcnow()
        test_period_end = now + timedelta(
            days=subscription_test_period_in_days
        )
        database.add_user(
            DBUser(
                user_id=event_from_user.id,
                name=name,
                role='user',
                birth_datetime=birth_datetime,
                birth_location=Location(
                    type='birth', 
                    **birth_location,
                    title=current_location_title
                ),
                current_location=Location(
                    type='current',
                    **current_location,
                    title=birth_location_title
                ),
                subscription_end_date=test_period_end.strftime(
                    database_datetime_format
                ),
                timezone_offset=get_timezone_offset(
                    **current_location
                ),
                every_day_prediction_time='7:30'
            )
        )
        await scheduler.add_send_message_job(
            user_id=event_from_user.id, 
            database=database,
            bot=bot
        )
        await state.update_data(
            prediction_access=True,
            subscription_end_date=test_period_end.strftime(
                database_datetime_format
            )
        )
        await main_menu(
            callback.message, 
            state,
            keyboards,
            bot
        )
    else:
        database.update_user_current_location(
            event_from_user.id, 
            Location(
                id=0,
                type='current', 
                **current_location,
                title=get_location_by_coords(**current_location)
            )
        )
        await scheduler.edit_send_message_job(
            user_id=event_from_user.id, 
            database=database,
            bot=bot
        )
        await main_menu(
            callback.message, 
            state,
            keyboards,
            bot
        )


@r.message(Command(commands=['menu']))
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


# Всякая хуйня которую я ещё не написал
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

