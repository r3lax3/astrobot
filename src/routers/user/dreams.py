from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User


from src.utils import path_validation
from src.routers.states import MainMenu
from src.database import Database
from src.astro_engine.moon import get_main_lunar_day_at_date
from src.keyboard_manager import KeyboardManager, bt


r = Router()

DREAMS_INTERPRETATIONS_FILEPATH = "./dreams.csv"
path_validation(DREAMS_INTERPRETATIONS_FILEPATH)

with open(DREAMS_INTERPRETATIONS_FILEPATH, "r", encoding="utf-8") as f:
    readlines = f.readlines()
    dreams_interpretations = list(
        map(
            lambda s: s.strip(), 
            readlines
        )
    )


@r.message(F.text, F.text == bt.dreams)
async def dreams_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)

    latitude = user.current_location.latitude
    longtitude = user.current_location.longitude

    now = datetime.utcnow() 

    lunar_day = get_main_lunar_day_at_date(now, latitude, longtitude)
    
    bot_message = await message.answer(
        text=dreams_interpretations[lunar_day.number - 1],
        reply_markup=keyboards.to_main_menu
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.end_action)

