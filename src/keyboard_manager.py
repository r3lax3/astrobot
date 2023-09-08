import datetime

from typing import List, Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.callback_data import CallbackData

from src.utils import split_list
from src.database import Database
from src.models import DateModifier


class KeyboardManager:
    def __init__(self, database: Database):
        self.database = database
        
        # Birth data

        self.start = self.build_keyboard_from_structure(
            [
                [
                    ('Ввести данные рождения', 'Ввести данные рождения')
                ]
            ],
            is_inline=True

        )

        self.choose_time = self.build_keyboard_from_structure(
            [
                [
                    ('Ночь', '1:00'),
                    ('Утро', '7:00')
                ],
                [
                    ('День', '13:00'),
                    ('Вечер', '19:00')
                ],
                [
                    '🔙 Назад'
                ]
            ],
            is_inline=True
        )

        # Main Menu
        self.main_menu = self.build_keyboard_from_structure(
            [
                ['🔮Прогноз'],
                ['💫 Сны', 'Карта Дня'],
                ['🌒 Общие прогнозы', '🌗 Луна в знаке'],
                ['✈️Смена часового пояса'],
                ['🔧 Техническая поддержка']
            ]
        )

        # Predict
        self.predict_choose_action = self.build_keyboard_from_structure(
            [
                ['🕓 Прогноз на дату'],
                ['⌚️ Ежедневный прогноз'],
                ['В главное меню']
            ]
        )
        self.predict_completed = self.build_keyboard_from_structure(
            [
                ['Проверить другую дату'],
                ['🌗 Луна в знаке', '🌒 Общие прогнозы'],
                ['🔙 Назад']
            ]
        )
        self.every_day_prediction_activated = self.build_keyboard_from_structure(
            [
                ['⌛Изменить время прогноза'],
                ['🔙 Назад']
            ]
        )

        # No category
        self.confirm = self.build_keyboard_from_structure(
            [
                ['Подтверждаю ☑'],
                ['Нет, вернуться назад ❎']
            ],
            is_inline=True
        )
        self.back = self.build_keyboard_from_structure(
            [
                ['🔙 Назад']
            ],
            is_inline=True
        )
        self.to_main_menu = self.build_keyboard_from_structure(
            [
                ['В главное меню']
            ],
            is_inline=True
        )

        self.reply_back = self.build_keyboard_from_structure(
            [
                ['🔙 Назад']
            ]
        )


    def predict_choose_date(self, date: str) -> InlineKeyboardMarkup:
        markup: InlineKeyboardMarkup = self.build_keyboard_from_structure(
            structure=[
                [
                    (date, "null")
                ],
                [
                    ('+1', DateModifier(modifier=1)),
                    ('+5', DateModifier(modifier=5)),
                    ('+10', DateModifier(modifier=10)),
                    ('+30', DateModifier(modifier=30)),
                ],
                [
                    ('-1', DateModifier(modifier=-1)),
                    ('-5', DateModifier(modifier=-5)),
                    ('-10', DateModifier(modifier=-10)),
                    ('-30', DateModifier(modifier=-30)),
                ],
                [
                    'Подтвердить'
                ],
                [
                    'Назад в меню'
                ]
            ],
            is_inline=True
        )
        return markup

    @staticmethod
    def pack_button(item: str | tuple, is_inline: bool):
        if is_inline:
            if isinstance(item, str):
                return InlineKeyboardButton(text=item, callback_data=item)
            elif isinstance(item, tuple):
                if isinstance(item[1], str):
                    return InlineKeyboardButton(text=item[0], callback_data=item[1])
                elif isinstance(item[1], CallbackData):
                    return InlineKeyboardButton(text=item[0], callback_data=item[1].pack())
        else:
            if isinstance(item, str):
                return KeyboardButton(text=item)
            else:
                Exception(f'Чет несоответствие типов какое-то. Ты написал что тип реплай, а пихаешь туда не str, а {type(item)}')

    def build_keyboard_from_structure(
            self, 
            structure: List[List[str | tuple]], 
            is_inline=False
    ) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
        """
        Help to construct keyboards in easy-way 
        """

        keyboard = []
        for row in structure:
            keyboard_row = [self.pack_button(item, is_inline) for item in row]
            keyboard.append(keyboard_row)
        
        markup: InlineKeyboardMarkup | ReplyKeyboardMarkup

        if is_inline:
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        else:
            markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        
        return markup
    
