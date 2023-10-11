from datetime import datetime

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message

from src import config


router = Router()
date_format: str = config.get('database.date_format')
datetime_format: str = config.get('database.datetime_format')


class DatetimeStringValidator(Filter):
    _datetime_format = None
    async def __call__(self, message: Message) -> bool:
        if self._datetime_format is None:
            raise NotImplementedError()

        parse_string: str = message.text

        try:
            datetime.strptime(parse_string, self._datetime_format)
        except:
            return False
        else:
            return True


class IsDate(DatetimeStringValidator):
    _datetime_format = date_format


class IsDatetime(DatetimeStringValidator):
    _datetime_format = datetime_format

