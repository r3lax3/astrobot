import asyncio
import logging
import sqlite3
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BufferedInputFile

from src import config
from src.database import Database
from src.database.models import User
from src.keyboard_manager import KeyboardManager
from src.middlewares import (AddDataInRedis,
                             ClearKeyboardFromMessageMiddleware,
                             DeleteMessagesMiddleware, MediaGroupMiddleware,
                             NullMiddleware, SkipGroupsUpdates)
from src.routers import admin_router, user_router
from src.scheduler import EveryDayPredictionScheduler

# from aiohttp import web

# from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application



ADMIN_CHAT_ID: int = config.get('admin_chat.id')
BACKUP_THREAD_ID: int = config.get('admin_chat.threads.backup')
DATABASE_DATETIME_FORMAT: str = config.get('database.datetime_format')
DATE_FORMAT: str = config.get('database.date_format')
TIME_FORMAT: str = config.get('database.time_format')

WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 8080
WEBHOOK_PATH = "/astrobot_webhook"
BASE_WEBHOOK_URL = "https://vm4720745.25ssd.had.wf"


# Database backup
async def backup_db(db: Database, bot: Bot):
    with sqlite3.connect(db.engine.url.database) as con:

        # Получаем дамп базы данных в виде строки
        db_str = '\n'.join(con.iterdump())

        await bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=BufferedInputFile(
                filename='backup_database.sql_dump',
                file=db_str.encode('utf-8')
            ),
            reply_to_message_id=BACKUP_THREAD_ID
        )


async def schedule_backup(db, bot, interval_seconds):
    while True:
        await backup_db(db, bot)
        await asyncio.sleep(interval_seconds)


# async def on_startup(bot: Bot) -> None:
#     # If you have a self-signed SSL certificate, then you will need to send a public
#     # certificate to Telegram
#     await bot.set_webhook(
#         f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
#     )


async def main():
    token: str = config.get('bot.token')
    bot = Bot(token, parse_mode='html')
    database = Database()

    scheduler = EveryDayPredictionScheduler(database, bot)
    scheduler.start()
    await scheduler.check_users_and_schedule()

    jobs = scheduler.get_jobs()
    print('\n\n')
    for job in jobs:
        print(f"ID: {job.id}, Next run: {job.next_run_time}, Job: {job.func.__name__}")
    print('\n\n')

    dp = Dispatcher(
        storage=RedisStorage.from_url('redis://localhost:6379'),
        database=database,
        keyboards=KeyboardManager(database),
        scheduler=scheduler
    )

    # Запускаем бекап базы данных каждые 6 часов.
    # 6 * 60 * 60 = 21600 секунд

    # asyncio.create_task(schedule_backup(db, bot, 21600))
    #
    await bot.get_updates(
        allowed_updates=[
            'message', 
            'callback_query'
        ]
    )

    # Message

    dp.message.middleware(MediaGroupMiddleware())
    dp.message.middleware(SkipGroupsUpdates())
    dp.message.middleware(DeleteMessagesMiddleware())
    dp.message.middleware(AddDataInRedis())

    # Callback

    dp.callback_query.middleware(NullMiddleware())
    dp.callback_query.middleware(DeleteMessagesMiddleware())
    dp.callback_query.middleware(ClearKeyboardFromMessageMiddleware())
    dp.callback_query.middleware(AddDataInRedis())

    # Include routers

    dp.include_routers(user_router, admin_router)

    # # Create aiohttp.web.Application instance
    # app = web.Application()
    # 
    # # Create an instance of request handler,
    # webhook_requests_handler = SimpleRequestHandler(
    #     dispatcher=dp,
    #     bot=bot
    # )
    #
    # # Register webhook handler on application
    # webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    #
    # # Mount dispatcher startup and shutdown hooks to aiohttp application
    # setup_application(app, dp, bot=bot)
    #
    # # And finally start webserver
    # web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, encoding="utf-8")
    asyncio.run(main())

