from datetime import datetime

from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config
from src.filters.is_date import IsDate, IsDatetime, IsTime
from src.filters.state_flag_filters import FSMFlagChecker
from src.filters.role import AdminFilter, UserFilter


database_datetime_format: str = config.get(
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
            database_datetime_format
        )
            
        return now < subscription_end_date

