import datetime as dt

from typing import Union

from aiogram import Bot
from aiogram.types import BufferedInputFile

from timezonefinder import TimezoneFinder

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src import config
from src.database import Database
from src.routers import messages
from src.routers.user.prediction import get_prediction_text


datetime_format: str = config.get('database.datetime_format')
date_format: str = config.get('database.date_format')
time_format: str = config.get('database.time_format')

TaskID = Union[str, tuple]
reminder_times = [36, 12]


class EveryDayPredictionScheduler(AsyncIOScheduler):
    """
    Scheduler to manage daily prediction messages and subscription 
    renewal reminders.
    """
    
    _timezone_finder = TimezoneFinder()

    def _get_timezone(
        self, 
        latitude: float, 
        longitude: float
    ) -> str | None:
        """Return the timezone for a given latitude and longitude."""
        return EveryDayPredictionScheduler._timezone_finder.timezone_at(
            lat=latitude, 
            lng=longitude
        )

    def _task_id_str(self, task_id: TaskID) -> str:
        """
        Convert a task ID into a string format suitable for the scheduler.
        """
        if isinstance(task_id, tuple):
            return "__".join(map(str, task_id))
        return task_id

    def add_task(
        self, 
        function, 
        trigger, 
        task_id: TaskID, 
        **kwargs
    ):
        """
        Add a new task to the scheduler using the provided details.
        """
        self.add_job(
            function, 
            trigger, 
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


    async def _send_message(
        self, 
        user_id: int, 
        database: Database, 
        bot: Bot
    ):
        """Send the daily prediction message to a user."""
        user = database.get_user(user_id=user_id)

        utc_target_date = dt.datetime.utcnow()
        target_date = utc_target_date + timedelta(hours=user.timezone_offset)
        target_date_str = target_date.strftime(date_format)

        photo = BufferedInputFile(
            generate_image_with_date_for_prediction(
                target_date_str
            ),
            filename='prediction_date.jpeg'
        )

        text: str = await get_prediction_text(
            target_date=target_date, 
            database=database, 
            user_id=user_id
        )
        await bot.send_photo(
            chat_id=user_id, 
            photo=photo,
            caption=text
        )

    async def _send_renewal_reminder(
        self, 
        user_id: int, 
        bot: Bot
    ):
        """
        Send a reminder to the user that their subscription is 
        about to end.
        """
        await bot.send_message(
            chat_id=user_id, 
            text=messages.renew_subscription_remind
        )

    async def add_send_message_job(
        self, 
        user_id: int, 
        database: Database, 
        bot: Bot
    ):
        """
        Add daily prediction and renewal reminder tasks for a user.
        """
        user = database.get_user(user_id=user_id)

        self.remove_task(str(user_id))
        for hours_before_end in reminder_times:
            self.remove_task(("reminder", user_id, hours_before_end))

        subscription_end_datetime = dt.datetime.strptime(
            user.subscription_end_date, 
            datetime_format
        )
        if not subscription_end_datetime > dt.datetime.utcnow():
            return

        current_location = database.get_location(
            location_id=user.current_location_id
        )

        timezone_str = self._get_timezone(
            longitude=current_location.longitude, 
            latitude=current_location.latitude
        )
        time = dt.datetime.strptime(
            user.every_day_prediction_time, 
            time_format
        )
        hour, minute = time.hour, time.minute
        self.add_task(
            self._send_message, 'cron', str(user_id), 
            hour=hour, minute=minute, 
            args=[user_id, database, bot], 
            timezone=timezone_str, 
            end_date=subscription_end_datetime
        )

        for hours_before_end in reminder_times:
            reminder_time = subscription_end_datetime - dt.timedelta(
                hours=hours_before_end
            )
            self.add_task(
                self._send_renewal_reminder, 
                'date', 
                (
                    "reminder", 
                    user_id, 
                    hours_before_end
                ), 
                run_date=reminder_time, 
                args=[user_id, bot], 
                timezone=timezone_str
            )

    async def edit_send_message_job(
        self, 
        user_id: int, 
        database: Database, 
        bot: Bot
    ):
        try:
            self.remove_task(str(user_id))
            for hours_before_end in reminder_times:
                self.remove_task(
                    (
                        "reminder",
                        user_id, 
                        hours_before_end
                    )
                )
        except JobLookupError:
            pass

        await self.add_send_message_job(user_id, database, bot)

