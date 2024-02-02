import asyncio
import os
import aiosqlite

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound

from src import config

ADMIN_CHAT_ID = config.get('admin_chat.id')
BACKUP_THREAD_ID = config.get('admin_chat.threads.backup')
TEMP_BACKUP_FILE_PATH = 'temp_database_backup.db'
DATABASE_FILE_PATH = 'database.db'


async def backup_db() -> bytes:
    # Connect to the existing database
    async with aiosqlite.connect(DATABASE_FILE_PATH) as existing_db:
        # Create a new connection for the backup file
        async with aiosqlite.connect(TEMP_BACKUP_FILE_PATH) as backup_db:
            # Perform the backup
            await existing_db.backup(backup_db)

    # Read the backup file's data as bytes
    with open(TEMP_BACKUP_FILE_PATH, 'rb') as f:
        backup_bytes = f.read()

    # Delete the backup file after use
    os.remove(TEMP_BACKUP_FILE_PATH)

    return backup_bytes


async def schedule_backup(bot: Bot, interval_seconds: int | float = 21600):
    while True:
        file = await backup_db()
        try:
            await bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=BufferedInputFile(
                    filename='database_backup.db',
                    file=file
                ),
                message_thread_id=BACKUP_THREAD_ID
            )
            await asyncio.sleep(interval_seconds)
        except (
            TelegramBadRequest,
            TelegramForbiddenError,
            TelegramNotFound
        ):
            break
