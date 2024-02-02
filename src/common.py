import os
import dotenv

from aiogram import Bot


dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN, parse_mode='html')
