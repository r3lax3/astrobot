from datetime import datetime

from aiogram.filters import BaseFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import config
from src.database import crud, Session
from src.filters.is_date import IsDate, IsDatetime, IsTime
from src.filters.role import AdminFilter, UserFilter
from src.filters.state_flag_filters import FSMFlagChecker

DATETIME_FORMAT: str = config.get("database.datetime_format")


class HaveActiveSubscription(Filter):
    async def __call__(
        self,
        obj: Message | CallbackQuery,
        state: FSMContext,
        event_from_user: User
    ):
        with Session() as session:
            user = crud.get_user(event_from_user.id, session)

        subscription_end = datetime.strptime(
            user.subscription_end_date,
            DATETIME_FORMAT
        )
        return subscription_end > datetime.utcnow()


class UserInDatabase(BaseFilter):
    async def __call__(
        self,
        obj: Message | CallbackQuery,
        database,
        event_from_user: User
    ):
        user = database.get_user(event_from_user.id)
        return user is not None
