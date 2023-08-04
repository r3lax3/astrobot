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

        # Получения данных рождения

        self.enter_birth_month = self.build_keyboard_from_structure(
            split_list(  # returned List[List[Tuple]]
                [
                    (month, str(number + 1))  # [ ("Январь", 1), ... ]
                    for number, month in enumerate(
                        [
                            'Январь',
                            'Февраль',
                            'Март',
                            'Апрель',
                            'Май',
                            'Июнь',
                            'Июль',
                            'Август',
                            'Сентябрь',
                            'Октябрь',
                            'Ноябрь',
                            'Декабрь'
                        ]
                    )
                ],
                sublist_len=2
            ) +
            [
                [ 'Назад' ]  # button Back under all
            ]  # Кнопка назад внизу
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
                    'Назад'
                ]
            ]
        )

        # Menu

        # Main Menu
        self.main_menu = self.build_keyboard_from_structure(
            [
                ['Прогнозы'],
                ['Сонник', 'Карта Дня'],
                ['Общий прогноз', 'Луна в знаке'],
                ['Техническая поддержка']
            ],
            markup_type='reply'
        )

        # Predict
        self.predict_choose_action = self.build_keyboard_from_structure(
            [
                ['Прогноз на дату'],
                ['Ежедневный прогноз']
            ],
            markup_type='reply'
        )
        self.predict_completed = self.build_keyboard_from_structure(
            [
                ['Проверить другую дату'],
                ['Луна в знаке', 'Общий прогноз'],
                ['Назад']
            ],
            markup_type='reply'
        )

        # No category

        self.confirm = self.build_keyboard_from_structure(
            [
                ['Подтверждаю'],
                ['Нет, вернуться назад']
            ]
        )
        self.back = self.build_keyboard_from_structure(
            [
                ['Назад']
            ]
        )
        self.to_main_menu = self.build_keyboard_from_structure(
            [
                ['В главное меню']
            ]
        )


    def predict_choose_date(self, date: str) -> InlineKeyboardMarkup:
        return self.build_keyboard_from_structure(
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
            markup_type='inline'
        )

    @staticmethod
    def pack_button(item: str | tuple, markup_type: str = 'inline'):
        if markup_type == 'inline':
            if isinstance(item, str):
                return InlineKeyboardButton(text=item, callback_data=item)
            elif isinstance(item, tuple):
                if isinstance(item[1], str):
                    return InlineKeyboardButton(text=item[0], callback_data=item[1])
                elif isinstance(item[1], CallbackData):
                    return InlineKeyboardButton(text=item[0], callback_data=item[1].pack())
        elif markup_type == 'reply':
            return KeyboardButton(text=item)

    def build_keyboard_from_structure(self, structure: List[List[str | tuple]], markup_type: str = 'inline'):
        """
        [
            ['Button1'],
            [('Button2', 'button2_callback_data'), 'Button3'],
            ['Button4', 'Button5', 'Button6']
        ]

        И вот эту всю хуйню оно превращает в кнопки.
        """

        keyboard = []
        for row in structure:
            keyboard_row = [self.pack_button(item, markup_type) for item in row]
            keyboard.append(keyboard_row)

        if markup_type == 'inline':
            return InlineKeyboardMarkup(inline_keyboard=keyboard)

        elif markup_type == 'reply':
            return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
