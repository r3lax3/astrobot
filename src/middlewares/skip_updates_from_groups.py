import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class SkipGroupsUpdates(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: Dict[str, Any],
    ) -> Any:
        if message.chat.type in ["group", "supergroup", "channel"]:
            logging.info("Скипаю апдейт т.к. групповой чат")
            return
        result = await handler(message, data)
        return result
