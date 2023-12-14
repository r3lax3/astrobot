from datetime import datetime

from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    User
)

from src import config, messages
from src.routers.states import MainMenu
from src.filters import IsTime
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt


database_datetime_format: str = config.get('database.datetime_format')
date_format: str = config.get('database.date_format')
TIME_FORMAT: str = config.get('database.time_format')

r = Router()


@r.message(
    MainMenu.prediction_every_day_enter_time,
    F.text,
    F.text == bt.back
)
@r.message(
    MainMenu.prediction_choose_action,
    F.text,
    F.text == bt.daily_prediction
)
async def every_day_prediction(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
):
    user = database.get_user(event_from_user.id)

    bot_message = await message.answer(
        messages.every_day_prediction_activated.format(
            send_time=user.every_day_prediction_time
        ),
        reply_markup=keyboards.back
    )

    await state.update_data(
        del_messages=[
            bot_message.message_id, 
            message.message_id
        ]
    )
    await state.set_state(MainMenu.prediction_every_day_enter_time)


@r.message(MainMenu.prediction_every_day_enter_time, F.text, IsTime())
async def enter_prediction_time(
    message: Message,
    database: Database,
    state: FSMContext,
    keyboards: KeyboardManager,
    scheduler,
    event_from_user: User,
    bot: Bot
):
    time = datetime.strptime(message.text, TIME_FORMAT)

    database.update_user_every_day_prediction_time(
        event_from_user.id,
        hour=time.hour, 
        minute=time.minute
    )
    await scheduler.edit_send_message_job(
        user_id=event_from_user.id,
        database=database,
        bot=bot
    )

    await every_day_prediction(
        message,
        state,
        keyboards,
        database,
        event_from_user
    )


