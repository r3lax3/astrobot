from datetime import datetime

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from src import config

DATE_FORMAT: str = config.get("database.date_format")
DATETIME_FORMAT: str = config.get("database.datetime_format")
TIME_FORMAT: str = config.get("database.time_format")


class DatetimeStringValidator(Filter):
    _format = None

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if self._format is None:
            raise NotImplementedError()
        if isinstance(event, Message):
            parse_string: str = event.text
        elif isinstance(event, CallbackQuery):
            parse_string: str = event.data

        try:
            datetime.strptime(parse_string, self._format)
        except:
            return False
        else:
            return True


class IsDate(DatetimeStringValidator):
    _format = DATE_FORMAT


class IsDatetime(DatetimeStringValidator):
    _format = DATETIME_FORMAT


class IsTime(DatetimeStringValidator):
    _format = TIME_FORMAT
