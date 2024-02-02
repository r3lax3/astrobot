from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from src import config
from src.astro_engine.moon import get_main_lunar_day_at_date
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import MainMenu
from src.utils import path_validation

r = Router()

DREAMS_INTERPRETATIONS_FILEPATH = "./dreams.csv"
DREAMS_IMAGE = config.get("files.dreams")
path_validation(DREAMS_INTERPRETATIONS_FILEPATH)

with open(DREAMS_INTERPRETATIONS_FILEPATH, "r", encoding="utf-8") as f:
    readlines = f.readlines()
    dreams_interpretations = list(map(lambda s: s.strip(), readlines))


@r.message(F.text, F.text == bt.dreams)
async def dreams_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database,
    event_from_user: User,
):
    user = database.get_user(event_from_user.id)

    latitude = user.current_location.latitude
    longtitude = user.current_location.longitude

    now = datetime.utcnow()

    lunar_day = get_main_lunar_day_at_date(now, latitude, longtitude)

    bot_message = await message.answer_photo(
        photo=DREAMS_IMAGE,
        caption=dreams_interpretations[lunar_day.number - 1],
        reply_markup=keyboards.to_main_menu,
    )
    await state.update_data(
        delete_keyboard_message_id=bot_message.message_id
    )
    await state.set_state(MainMenu.end_action)

