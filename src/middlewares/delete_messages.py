from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
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

        del_messages = state_data.get('del_messages', [])
        
        user: User = data["event_from_user"]
        bot = data['bot']
        
        if isinstance(del_messages, list):
            for message_id in del_messages:
                try:
                    await bot.delete_message(chat_id=user.id, message_id=message_id)
                except TelegramBadRequest:
                    pass

        result = await handler(event, data)
        if not isinstance(event, Message):
            return result
        if event.text and event.text.startswith('/'):
            return result
        else:
            try:
                await bot.delete_message(chat_id=user.id, message_id=event.message_id)
            except TelegramBadRequest:
                pass
            return result

