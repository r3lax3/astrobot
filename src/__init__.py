import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
from aiogram.fsm.storage.redis import RedisStorage

from src import config
from src.routers import user_router
from src.database import Database
from src.scheduler import EveryDayPredictionScheduler
from src.keyboard_manager import KeyboardManager
from src.middlewares import (
    DeleteMessagesMiddleware, 
    MediaGroupMiddleware, 
    SkipAdminchatUpdates,
    NullMiddleware,
    PredictionMessageDeleteKeyboardMiddleware
)


admin_chat_id: int = config.get('admin_chat.id')
backup_thread_id: int = config.get('admin_chat.threads.backup')
database_datetime_format: str = config.get('database.datetime_format')
date_format: str = config.get('database.date_format')
time_format: str = config.get('database.time_format')


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


async def check_users_and_schedule(
    scheduler: EveryDayPredictionScheduler, 
    database: Database, 
    bot: Bot
):
    rows = database.execute_query(
        query="SELECT user_id, every_day_prediction_time FROM users",
        fetchall=True
    )
    for row in rows:
        user_id, time_str = row
        await scheduler.add_send_message_job(
            user_id, 
            time_str, 
            database, 
            bot
        )


async def main():
    token: str = config.get('bot.token')
    bot = Bot(token, parse_mode='html')
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
    await bot.get_updates(
        allowed_updates=[
            'message', 
            'callback_query'
        ]
    )

    # Album handler
    dp.message.middleware(MediaGroupMiddleware())

    # If null in callback - pass event
    dp.callback_query.middleware(NullMiddleware())

    # One-screen logic
    dp.message.middleware(DeleteMessagesMiddleware())
    dp.callback_query.middleware(DeleteMessagesMiddleware())

    # Admin chat updates skip
    dp.message.middleware(SkipAdminchatUpdates())
    dp.callback_query.middleware(PredictionMessageDeleteKeyboardMiddleware())

    dp.include_router(user_router)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        scheduler.shutdown()

