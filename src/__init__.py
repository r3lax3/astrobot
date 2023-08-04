import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage

from src import config
from src.routers import admin_router, user_router
from src.database import Database
from src.keyboard_manager import KeyboardManager
from src.middlewares import DeleteMessagesMiddleware, MediaGroupMiddleware, SkipAdminchatUpdates


admin_chat_id = config.get('admin_chat.id')
backup_thread_id = config.get('admin_chat.threads.backup')


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


async def main():
    bot = Bot(config.get('bot.token'), parse_mode='html')
    db = Database()
    dp = Dispatcher(
        storage=RedisStorage.from_url('redis://localhost:6379'),
        database=db,
        keyboards=KeyboardManager(db)
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

    await dp.start_polling(bot)
