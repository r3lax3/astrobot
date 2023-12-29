from aiogram import Bot, types
from aiogram.filters import BaseFilter

from src.database import Database


class IsNotSub(BaseFilter):
    async def __call__(
        self,
        event: types.TelegramObject,
        event_from_user: types.User,
        database: Database,
        bot: Bot,
    ):
        channels = database.get_mandatory_channels()
        for channel in channels:
            if isinstance(
                await bot.get_chat_member(channel.channel_id, event_from_user.id),
                (types.ChatMemberBanned, types.ChatMemberLeft),
            ):
                return True
        return False
