import asyncio
import os

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage

from aiohttp import web
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application
)

from src import config
from src.common import bot
from src.database import Database, schedule_backup
from src.keyboard_manager import KeyboardManager
from src.middlewares import (
    AddDataInRedis,
    ClearKeyboardFromMessageMiddleware,
    DeleteMessagesMiddleware,
    MediaGroupMiddleware,
    NullMiddleware,
    SkipGroupsUpdates
)
from src.routers import admin_router, user_router
from src.scheduler import EveryDayPredictionScheduler
from src.utils import logger_settings
from src.payments import ProdamusPaymentService
from src.payments.gatebot_sync import handle_gatebot_subscription_sync


WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

WEB_SERVER_HOST = config.get('webhook.web_server_host')
WEB_SERVER_PORT = config.get('webhook.web_server_port')

BASE_WEBHOOK_PATH = config.get('webhook.base_webhook_url')

BOT_WEBHOOK_PATH = "/bot"
PAYMENT_WEBHOOK_PATH = '/payments'
GATEBOT_SYNC_WEBHOOK_PATH = '/gatebot/sync'

DO_BACKUP = config.get('database.do_backup')


async def on_startup(bot: Bot, scheduler: EveryDayPredictionScheduler) -> None:
    await bot.set_webhook(
        f"{BASE_WEBHOOK_PATH}{BOT_WEBHOOK_PATH}",
        allowed_updates=['message', 'callback_query'],
        drop_pending_updates=True
    )
    scheduler.start()
    asyncio.create_task(scheduler.check_users_and_schedule())

    if DO_BACKUP:
        asyncio.create_task(schedule_backup(bot))


async def on_shutdown(bot: Bot, scheduler: EveryDayPredictionScheduler):
    await bot.delete_webhook()

    if scheduler.running:
        scheduler.shutdown(wait=False)

    # aiogram's setup_application only emits the dispatcher shutdown; it does
    # not close the bot's aiohttp session. Close it explicitly to avoid the
    # "Unclosed client session"/"Unclosed connector" warnings on exit.
    await bot.session.close()


def main():
    scheduler = EveryDayPredictionScheduler()

    dp = Dispatcher(
        storage=RedisStorage.from_url('redis://localhost:6379'),
        database=Database,
        keyboards=KeyboardManager(Database),
        scheduler=scheduler
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

    # Create aiohttp.web.Application instance
    app = web.Application()

    app.add_routes(
        [
            web.post(
                PAYMENT_WEBHOOK_PATH,
                ProdamusPaymentService.handle_payment_update
            ),
            web.post(
                GATEBOT_SYNC_WEBHOOK_PATH,
                handle_gatebot_subscription_sync
            )
        ]
    )

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Create an instance of request handler,
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )

    # Register webhook handler on application
    webhook_requests_handler.register(app, path=BOT_WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    try:
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    except OSError as e:
        if e.errno == 98:
            import logging
            logging.getLogger(__name__).critical(
                f"Port {WEB_SERVER_PORT} is already in use. "
                f"Kill the existing process with: "
                f"lsof -ti :{WEB_SERVER_PORT} | xargs kill"
            )
        raise


if __name__ == '__main__':
    logger_settings()
    main()
