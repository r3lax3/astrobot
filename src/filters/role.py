from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, User

from src import config


admins_ids_list = config.get('admins.ids')


class AdminFilter(BaseFilter):
    async def __call__(
        self, 
        obj: Message | CallbackQuery, 
        event_from_user: User
    ):
        return event_from_user.id in admins_ids_list


class UserFilter(BaseFilter):
    async def __call__(
        self, 
        obj: Message | CallbackQuery, 
        event_from_user: User
    ):
        return not (event_from_user.id  in admins_ids_list)

