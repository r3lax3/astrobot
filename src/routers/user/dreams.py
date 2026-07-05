from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from src import config, paths
from src.astro_engine.moon import get_main_lunar_day_at_date
from src.keyboards import keyboards, bt
from src.routers.states import MainMenu


r = Router()


DREAMS_IMAGE = config.get("files.dreams")

with open(paths.DREAMS_INTERPRETATIONS_FILE, "r", encoding="utf-8") as f:
    dreams_interpretations = [line.strip() for line in f]


@r.message(F.text, F.text == bt.dreams)
async def dreams_menu(
    message: Message,
    state: FSMContext,
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
        reply_markup=keyboards.to_main_menu(),
    )
    await state.update_data(
        delete_keyboard_message_id=bot_message.message_id
    )
    await state.set_state(MainMenu.end_action)
