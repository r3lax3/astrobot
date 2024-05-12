from tqdm import tqdm

import pytz
import logging

from datetime import datetime, timedelta
from typing import Union

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from aiogram.types import BufferedInputFile
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src import config, messages
from src.database import Session, crud
from src.database.models import User
from src.enums import FileName
from src.image_processing import get_image_with_astrodata
from src.routers.user.prediction.text_formatting import get_prediction_text
from src.utils import get_timezone_str_from_offset, format_time_delta
from src.keyboards import keyboards


LOGGER = logging.getLogger(__name__)

DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
TIME_FORMAT: str = config.get("database.time_format")

TaskID = Union[str, tuple]
REMINDER_TIMES = [36, 12]


class EveryDayPredictionScheduler(AsyncIOScheduler):
    """
    Scheduler to manage daily prediction messages and subscription
    renewal reminders.
    """

    def __init__(self, bot: Bot):
        super().__init__()

        self.bot = bot

    def _task_id_str(self, task_id: TaskID) -> str:
        """
        Convert a task ID into a string format suitable for the scheduler.
        """
        if isinstance(task_id, tuple):
            return "__".join(map(str, task_id))
        return task_id

    def add_task(self, function, trigger, task_id: TaskID, **kwargs):
        """
        Add a new task to the scheduler using the provided details.
        """
        self.add_job(
            function,
            trigger,
            misfire_grace_time=100000,
            max_instances=100000,
            id=self._task_id_str(task_id),
            **kwargs
        )

    def remove_task(self, task_id: TaskID):
        """Remove an existing task using its ID."""
        try:
            self.remove_job(job_id=self._task_id_str(task_id))
        except JobLookupError:
            # Если задача не найдена, не делать ничего
            pass

    async def set_all_jobs(self, user_id: int):
        await self.delete_reminder_jobs(user_id)
        await self.delete_send_message_job(user_id)

        with Session() as session:
            user = crud.get_user(user_id=user_id, session=session)

            await self.add_send_message_job(user)
            await self.add_reminder_jobs(user)

    async def check_users_and_schedule(self):
        with Session() as session:
            rows = session.query(User.user_id).all()
            if rows:
                for row in tqdm(rows, desc="Scheduling Jobs"):
                    user_id = row[0]
                    await self.set_all_jobs(user_id)

        LOGGER.info("Scheduling completed for all users.")

    async def send_message(self, user: User):
        """Send the daily prediction message to a user."""
        with Session() as session:
            user = crud.get_user(user_id=user.user_id, session=session)

            user_id = user.user_id

            utc_target_date = datetime.utcnow()
            target_datetime = utc_target_date + timedelta(
                hours=user.timezone_offset
            )
            target_date = target_datetime.date()

            photo_bytes = await get_image_with_astrodata(user)

            photo = BufferedInputFile(
                file=photo_bytes,
                filename=FileName.PREDICTION.value
            )

            subscription_end_datetime = datetime.strptime(
                user.subscription_end_date,
                DATETIME_FORMAT
            )
            try:
                if datetime.utcnow() < subscription_end_datetime:
                    text = await get_prediction_text(
                        date=target_date,
                        database=crud,
                        user_id=user_id
                    )
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        reply_markup=keyboards.main_menu()
                    )
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=keyboards.main_menu()
                    )

                else:
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        reply_markup=keyboards.main_menu()
                    )

            except TelegramForbiddenError:
                LOGGER.info(f'User {user.name} blocked bot')

            else:
                LOGGER.info(
                    f'User {user.name} getted every day prediction '
                    f'at {target_datetime.strftime(DATETIME_FORMAT)}'
                )

    async def send_renewal_reminder(self, user_id: int):
        """
        Send a reminder to the user that their subscription is
        about to end.
        """
        await self.bot.send_message(
            chat_id=user_id,
            text=messages.RENEW_SUBSCRIPTION_REMIND,
            reply_markup=keyboards.main_menu()
        )

    async def add_send_message_job(self, user: User):
        """
        Add daily prediction and renewal reminder tasks for a user.
        """
        timezone_str = get_timezone_str_from_offset(user.timezone_offset)

        time = datetime.strptime(user.every_day_prediction_time, TIME_FORMAT)

        self.add_task(
            self.send_message,
            "cron",
            str(user.user_id),
            hour=time.hour,
            minute=time.minute,
            args=[user],
            timezone=timezone_str,
        )

        job = self.get_job(str(user.user_id))
        now = datetime.now(pytz.timezone(timezone_str))
        delta = job.next_run_time - now

        LOGGER.info(f'До отправки {format_time_delta(delta)}')

    async def add_reminder_jobs(self, user: User):
        subscription_end_datetime = datetime.strptime(
            user.subscription_end_date,
            DATETIME_FORMAT
        )

        timezone_str = get_timezone_str_from_offset(user.timezone_offset)

        now = datetime.utcnow()

        for hours_before_end in REMINDER_TIMES:
            reminder_time = subscription_end_datetime - timedelta(
                hours=hours_before_end
            )
            if reminder_time > now:
                self.add_task(
                    self.send_renewal_reminder,
                    "date",
                    ("reminder", user.user_id, hours_before_end),
                    run_date=reminder_time,
                    args=[user.user_id],
                    timezone=timezone_str,
                )

    async def delete_reminder_jobs(self, user_id: int):
        for hours_before_end in REMINDER_TIMES:
            self.remove_task(("reminder", user_id, hours_before_end))

    async def delete_send_message_job(self, user_id: int):
        self.remove_task(str(user_id))
