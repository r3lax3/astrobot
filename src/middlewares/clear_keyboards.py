from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, TelegramObject


class ClearKeyboardFromMessageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        state = data['state']
        state_data = await state.get_data()
        delete_keyboard_message_id = state_data.get('delete_keyboard_message_id', None)
        
        if delete_keyboard_message_id is not None:
            bot: Bot = data['bot']
            event_from_user = data['event_from_user']
            try:
                await bot.edit_message_reply_markup(
                    chat_id=event_from_user.id,
                    message_id=delete_keyboard_message_id,
                    reply_markup=None
                )
                await state.update_data(delete_keyboard_message_id=None)
            except TelegramBadRequest:
                pass
        result = await handler(event, data)

        return result
