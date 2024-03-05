from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from src import config, messages
from src.database import crud, Session
from src.filters import IsTime
from src.keyboards import keyboards, bt
from src.routers.states import MainMenu

database_datetime_format: str = config.get("database.datetime_format")
date_format: str = config.get("database.date_format")
TIME_FORMAT: str = config.get("database.time_format")

r = Router()


@r.message(MainMenu.prediction_every_day_enter_time, F.text, F.text == bt.back)
@r.message(MainMenu.prediction_choose_action, F.text, F.text == bt.daily_prediction)
async def every_day_prediction(
    message: Message,
    state: FSMContext,
    event_from_user: User,
):
    with Session() as session:
        user = crud.get_user(event_from_user.id, session)

    bot_message = await message.answer(
        messages.EVERY_DAY_PREDICTION_ACTIVATED.format(
            send_time=user.every_day_prediction_time
        ),
        reply_markup=keyboards.back(),
    )

    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(MainMenu.prediction_every_day_enter_time)


@r.message(MainMenu.prediction_every_day_enter_time, F.text, IsTime())
async def enter_prediction_time(
    message: Message,
    state: FSMContext,
    scheduler,
    event_from_user: User,
):
    time = datetime.strptime(message.text, TIME_FORMAT)

    crud.update_user_every_day_prediction_time(
        event_from_user.id, hour=time.hour, minute=time.minute
    )
    await scheduler.set_all_jobs(user_id=event_from_user.id)

    await every_day_prediction(message, state, event_from_user)
