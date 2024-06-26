import os
import dotenv

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from src.utils import get_day_selection_database


dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='html'))

DAY_SELECTION_DATABASE: dict[str, dict] = get_day_selection_database()

