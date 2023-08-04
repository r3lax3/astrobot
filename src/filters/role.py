from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery, User

from src.database import Database


class RoleFilter(Filter):
    def __init__(self, role):
        self.role = role

    async def __call__(self, obj: Message | CallbackQuery, event_from_user: User, database: Database):
        user = database.get_users(role=self.role, user_id=event_from_user.id)
        return bool(user)


class AdminFilter(Filter):
    async def __call__(self, obj: Message | CallbackQuery, event_from_user: User, database: Database):
        user = database.get_users(role='admin', user_id=event_from_user.id)
        return bool(user)


class MasterFilter(Filter):
    async def __call__(self, obj: Message | CallbackQuery, database: Database, event_from_user: User):
        user = database.get_users(role='master', user_id=event_from_user.id)
        return bool(user)
