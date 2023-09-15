import datetime as dt
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from timezonefinder import TimezoneFinder

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
from aiogram.fsm.storage.redis import RedisStorage

from src import config
from src.routers import user_router
from src.routers.user.prediction import get_prediction_text
from src.database import Database
from src.keyboard_manager import KeyboardManager
from src.middlewares import DeleteMessagesMiddleware, MediaGroupMiddleware, SkipAdminchatUpdates


class EveryDayPredictionScheduler(AsyncIOScheduler):
    _timezone_finder = TimezoneFinder()

    def _get_timezone(self, latitude, longitude) -> str:
        return EveryDayPredictionScheduler._timezone_finder.timezone_at(
            lat=latitude, 
            lng=longitude
        )  # Получаем имя временной зоны

    # Every day prediction
    async def _send_message(self, user_id, database, bot):
        print('процесс заработал')
        target_date = dt.datetime.now().strftime(date_format)
        text: str = await get_prediction_text(
            target_date=target_date,
            database=database,
            user_id=user_id
            )

        await bot.send_message(chat_id=user_id, text=text) 

    async def add_send_message_job(self, user_id: int, time_str: str, database: Database, bot: Bot):
        hours, minutes = map(int, time_str.split(':'))

        user = database.get_user(user_id=user_id)
        current_location = database.get_location(location_id=user.current_location_id)
        timezone_str = self._get_timezone(longitude=current_location.longitude, latitude=current_location.latitude)
        return self.add_job(
            self._send_message, 
            'cron', 
            hour=hours, 
            minute=minutes, 
            args=[user_id, database, bot], 
            id=str(user_id),
            timezone=timezone_str
        )


admin_chat_id: int = config.get('admin_chat.id')
backup_thread_id: int = config.get('admin_chat.threads.backup')
database_datetime_format: str = config.get('database.datetime_format')
date_format: str = config.get('database.date_format')


# Database backup
async def backup_db(db: Database, bot: Bot):
    db_str = '\n'.join(list(db.connection.iterdump()))

    await bot.send_document(
        chat_id=admin_chat_id,
        document=BufferedInputFile(
            filename='backup_database.sql_dump',
            file=db_str.encode('utf-8')
        ),
        reply_to_message_id=backup_thread_id
    )


async def schedule_backup(db, bot, interval_seconds):
    while True:
        await backup_db(db, bot)
        await asyncio.sleep(interval_seconds)


async def check_users_and_schedule(scheduler: EveryDayPredictionScheduler, database: Database, bot: Bot):
    rows = database.execute_query(
        query="SELECT user_id, every_day_prediction_time FROM users",
        fetchall=True
    )

    for row in rows:
        user_id, time_str = row
        await scheduler.add_send_message_job(user_id, time_str, database, bot)    


async def main():
    bot = Bot(config.get('bot.token'), parse_mode='html')
    bot_instance = await bot.me()
    config.set('bot.username', bot_instance.username)

    database = Database()

    scheduler = EveryDayPredictionScheduler()

    await check_users_and_schedule(scheduler, database, bot)

    scheduler.start()

    dp = Dispatcher(
        storage=RedisStorage.from_url('redis://localhost:6379'),
        database=database,
        keyboards=KeyboardManager(database),
        scheduler=scheduler
    )

    # Запускаем бекап базы данных каждые 6 часов.
    # 6 * 60 * 60 = 21600 секунд

    # asyncio.create_task(schedule_backup(db, bot, 21600))
    await bot.get_updates(allowed_updates=['message', 'callback_query'])

    # Album handler
    dp.message.middleware(MediaGroupMiddleware())

    # One-screen logic
    dp.message.middleware(DeleteMessagesMiddleware())
    dp.callback_query.middleware(DeleteMessagesMiddleware())

    # Admin chat updates skip
    dp.message.middleware(SkipAdminchatUpdates())

    dp.include_router(user_router)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        scheduler.shutdown()

