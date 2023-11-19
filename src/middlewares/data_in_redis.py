from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.database import Database


class AddDataInRedis(BaseMiddleware):
    keys_list = [
        'timezone_offset'
    ]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        state = data['state']
        state_data = await state.get_data()

        database: Database = data['database']
        
        missing_keys = []
    
        for key in self.keys_list:
            if state_data.get(key, None) is None:
                missing_keys.append(key)

        for key in missing_keys:
            match key:
                case 'timezone_offset':
                    user = database.get_user(user_id = event.from_user.id)
                    
                    if user:
                        await state.update_data(timezone_offset=user.timezone_offset)

        result = await handler(event, data)
        return result

