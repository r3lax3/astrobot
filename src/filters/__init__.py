from datetime import datetime

from aiogram.filters import BaseFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import config
from src.database import Database
from src.filters.is_date import IsDate, IsDatetime, IsTime
from src.filters.state_flag_filters import FSMFlagChecker
from src.filters.role import AdminFilter, UserFilter


DATETIME_FORMAT: str = config.get(
    'database.datetime_format'
)

class HasPredictionAccess(Filter):
    async def __call__(
        self, 
        obj: Message | CallbackQuery, 
        state: FSMContext
    ):
        data = await state.get_data()

        now = datetime.utcnow()

        subscription_end_date_str = data['subscription_end_date']
        subscription_end_date = datetime.strptime(
            subscription_end_date_str,
            DATETIME_FORMAT
        )
            
        return now < subscription_end_date

class UserInDatabase(BaseFilter):
    async def __call__(
        self, 
        obj: Message | CallbackQuery, 
        database: Database,
        event_from_user: User
    ):
        user = database.get_user(event_from_user.id)
        return user is not None

