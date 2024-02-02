import validators
from typing import List

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters.callback_data import CallbackData


def validate_link(link: str) -> bool:
    return validators.url(link) or validators.domain(link)


class KeyboardBuilder:
    """
    Help to construct keyboards in easy-way
    """
    @staticmethod
    def pack_button(
        item: str | tuple,
        is_inline: bool
    ):
        if is_inline:
            if isinstance(item, str):
                return InlineKeyboardButton(
                    text=item,
                    callback_data=item
                )
            elif isinstance(item, tuple):
                if isinstance(item[1], str):
                    if validate_link(item[1]):
                        return InlineKeyboardButton(
                            text=item[0],
                            url=item[1]
                        )
                    else:
                        return InlineKeyboardButton(
                            text=item[0],
                            callback_data=item[1]
                        )
                elif isinstance(item[1], CallbackData):
                    return InlineKeyboardButton(
                        text=item[0],
                        callback_data=item[1].pack()
                    )
        else:
            if isinstance(item, str):
                return KeyboardButton(text=item)
            else:
                Exception(
                    'Чет несоответствие типов какое-то. Ты написал что тип реплай,'
                    f'а пихаешь туда не str, а {type(item)}'
                )

    @staticmethod
    def build(
        structure: List[List[str | tuple[str, str | CallbackData]]],
        is_inline=False,
        **kwargs
    ) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
        keyboard = []

        for row in structure:
            keyboard_row = [KeyboardBuilder.pack_button(item, is_inline) for item in row]
            keyboard.append(keyboard_row)

        markup: InlineKeyboardMarkup | ReplyKeyboardMarkup

        if is_inline:
            markup = InlineKeyboardMarkup(
                inline_keyboard=keyboard,
                **kwargs
            )

        else:
            markup = ReplyKeyboardMarkup(
                keyboard=keyboard,
                resize_keyboard=True,
                **kwargs
            )

        return markup
