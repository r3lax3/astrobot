from datetime import datetime

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message

from src import config

router = Router()
date_format: str = config.get('database.date_format')


class IsDate(Filter):
    async def __call__(self, message: Message) -> bool:
        parse_string: str = message.text
        try:
            datetime.strptime(parse_string, date_format)
        except:
            return False
        else:
            return True

