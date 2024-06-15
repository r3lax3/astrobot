from datetime import datetime

from aiogram.types import TelegramObject, User
from aiogram.filters import BaseFilter

from src import config
from src.database import Session, crud


DATETIME_FORMAT = config.get("database.datetime_format")


class HaveActiveSubscription(BaseFilter):
    async def __call__(
        self,
        event: TelegramObject,
        event_from_user: User,
    ):
        with Session() as session:
            user = crud.get_user(event_from_user.id, session)

        subscription_end = datetime.strptime(
            user.subscription_end_date,
            DATETIME_FORMAT
        )
        return subscription_end > datetime.utcnow()
