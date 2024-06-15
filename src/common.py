import os
import dotenv

from aiogram import Bot

from src.utils import get_day_selection_database


dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN, parse_mode='html')

DAY_SELECTION_DATABASE: dict[str, dict] = get_day_selection_database()

