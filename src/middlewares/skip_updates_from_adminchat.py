import logging

from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, User, Message

from src import config


class SkipAdminchatUpdates(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any]
    ) -> Any:
        if message.chat.id == config.get('admin_chat.id'):
            logging.info('Скипаю апдейт т.к. админ чат')
            return
        result = await handler(message, data)
        return result
