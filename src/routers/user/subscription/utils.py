from datetime import datetime, timedelta

from src import messages, config
from src.database.models import User


DATETIME_FORMAT = config.get("database.datetime_format")


def get_subscription_status_text(user: User):

    user_subscription_end_datetime = (
        datetime.strptime(
            user.subscription_end_date,
            DATETIME_FORMAT
        )
    )

    utcnow = datetime.utcnow()
    if utcnow > user_subscription_end_datetime:
        return messages.SUBSCRIPTION_STATUS_NOT_ACTIVE
    else:
        timezone_offset = timedelta(hours=user.timezone_offset)

        subscription_end_datetime = (
            user_subscription_end_datetime + timezone_offset
        ).strftime(DATETIME_FORMAT)
        return messages.SUBSCRIPTION_STATUS_ACTIVE.format(
            subscription_end_datetime=subscription_end_datetime
        )
