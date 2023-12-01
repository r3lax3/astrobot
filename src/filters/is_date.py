from datetime import datetime

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message

from src import config


router = Router()
date_format: str = config.get('database.date_format')
datetime_format: str = config.get('database.datetime_format')
time_format: str = config.get('database.time_format')


class DatetimeStringValidator(Filter):
    _format = None
    async def __call__(self, message: Message) -> bool:
        if self._format is None:
            raise NotImplementedError()

        parse_string: str = message.text

        try:
            datetime.strptime(parse_string, self._format)
        except ValueError:
            return False
        else:
            return True


class IsDate(DatetimeStringValidator):
    _format = date_format


class IsDatetime(DatetimeStringValidator):
    _format = datetime_format

class IsTime(DatetimeStringValidator):
    _format = time_format

