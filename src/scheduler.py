import datetime as dt

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from timezonefinder import TimezoneFinder
from aiogram import Bot

from src import config
from src.database import Database
from src.routers.user.prediction import get_prediction_text


date_format: str = config.get('database.date_format')
time_format: str = config.get('database.time_format')


class EveryDayPredictionScheduler(AsyncIOScheduler):
    _timezone_finder = TimezoneFinder()

    def _get_timezone(self, latitude: float, longitude: float) -> str | None:
        # Получаем имя временной зоны
        return EveryDayPredictionScheduler._timezone_finder.timezone_at(
            lat=latitude, 
            lng=longitude
        )

    # Every day prediction
    async def _send_message(
        self, 
        user_id: int, 
        database: Database,
        bot: Bot
    ):
        target_date = dt.datetime.now()
        text: str = await get_prediction_text(
            target_date=target_date,
            database=database,
            user_id=user_id
        )
        await bot.send_message(chat_id=user_id, text=text) 

    async def add_send_message_job(
        self, 
        user_id: int,
        database: Database,
        bot: Bot
    ):
        user = database.get_user(user_id=user_id)
        subscription_end_datetime = dt.datetime.strptime(
            user.subscription_end_date, 
            "%d.%m.%Y %H:%M"
        )
        
        time = dt.datetime.strptime(
            user.every_day_prediction_time, 
            time_format
        )

        hour = time.hour
        minute = time.minute

        current_location = database.get_location(
            location_id=user.current_location_id
        )
        timezone_str = self._get_timezone(
            longitude=current_location.longitude, 
            latitude=current_location.latitude
        )

        return self.add_job(
            self._send_message, 
            'cron', 
            hour=hour, 
            minute=minute, 
            args=[user_id, database, bot], 
            id=str(user_id),
            timezone=timezone_str,
            end_date=subscription_end_datetime
        )
    
    async def edit_send_message_job(
        self, 
        user_id: int,
        database: Database,
        bot: Bot
    ):
        self.remove_job(job_id=str(user_id))
        await self.add_send_message_job(user_id, database, bot)


