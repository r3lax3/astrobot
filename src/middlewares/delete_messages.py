import logging

from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, User, Message


class DeleteMessagesMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        state_data = await data['state'].get_data()
        messages_ids = state_data.get('del_messages', [])
        user: User = data["event_from_user"]
        bot = data['bot']

        for message_id in messages_ids:
            try:
                await bot.delete_message(chat_id=user.id, message_id=message_id)
            except TelegramBadRequest:
                pass

        result = await handler(event, data)
        if isinstance(event, Message):
            if not (event.text and event.text.startswith('/')):
                try:
                    await bot.delete_message(chat_id=user.id, message_id=event.message_id)
                except TelegramBadRequest:
                    pass
        return result

