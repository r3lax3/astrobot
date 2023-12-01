import asyncio
import sys
import logging
import sqlite3

# from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
from aiogram.fsm.storage.redis import RedisStorage
# from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from src import config
from src.routers import user_router, admin_router
from src.database import Database
from src.database.models import User
from src.scheduler import EveryDayPredictionScheduler
from src.keyboard_manager import KeyboardManager
from src.middlewares import (
    DeleteMessagesMiddleware, 
    MediaGroupMiddleware, 
    SkipGroupsUpdates,
    NullMiddleware,
    PredictionMessageDeleteKeyboardMiddleware,
    AddDataInRedis
)


admin_chat_id: int = config.get(
    'admin_chat.id'
)
backup_thread_id: int = config.get(
    'admin_chat.threads.backup'
)
database_datetime_format: str = config.get(
    'database.datetime_format'
)
date_format: str = config.get(
    'database.date_format'
)
time_format: str = config.get(
    'database.time_format'
)

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
    rows = database.session.query(
        User.user_id
    ).all()
    for row in rows:
        user_id = row[0]
        await scheduler.add_send_message_job(
            user_id, 
            database, 
            bot
        )


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

    scheduler = EveryDayPredictionScheduler()

    await check_users_and_schedule(scheduler, database, bot)

    scheduler.start()

    dp = Dispatcher(
        storage=RedisStorage.from_url(
            'redis://localhost:6379'
        ),
        database=database,
        keyboards=KeyboardManager(database),
        scheduler=scheduler
    )

    # Запускаем бекап базы данных каждые 6 часов.
    # 6 * 60 * 60 = 21600 секунд

    # asyncio.create_task(schedule_backup(db, bot, 21600))
    #
    # await bot.get_updates(
    #     allowed_updates=[
    #         'message', 
    #         'callback_query'
    #     ]
    # )

    # Message

    dp.message.middleware(
        MediaGroupMiddleware()
    )
    dp.message.middleware(
        SkipGroupsUpdates()
    )
    dp.message.middleware(
        DeleteMessagesMiddleware()
    )
    dp.message.middleware(
        AddDataInRedis()
    )

    # Callback

    dp.callback_query.middleware(
        NullMiddleware()
    )
    dp.callback_query.middleware(
        DeleteMessagesMiddleware()
    )
    dp.callback_query.middleware(
        PredictionMessageDeleteKeyboardMiddleware()
    )
    dp.callback_query.middleware(
        AddDataInRedis()
    )

    # Include routers

    dp.include_routers(
        user_router,
        admin_router
    )
    #
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
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

