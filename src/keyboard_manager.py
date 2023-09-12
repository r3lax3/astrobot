from typing import List

from types import SimpleNamespace

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, message
from aiogram.filters.callback_data import CallbackData

from src.database import Database
from src.models import DateModifier, SubscriptionPeriod


buttons_text = {
    'enter_birth_data':     'Ввести данные рождения',
    'night':                'Ночь',
    'morning':              'Утро',
    'day':                  'День',
    'evening':              'Вечер',
    'back':                 '🔙 Назад',
    'subscription':         '🌟Подписка',
    'forecast':             '🔮Прогноз',
    'dreams':               '💫 Сны',
    'card_of_the_day':      '🃏Карта Дня',
    'general_forecasts':    '🌒 Общие прогнозы',
    'moon_in_sign':         '🌗 Луна в знаке',
    'change_timezone':      '✈️Смена часового пояса',
    'tech_support':         '🔧 Техническая поддержка',
    'forecast_for_date':    '🕓 Прогноз на дату',
    'daily_forecast':       '⌚️ Ежедневный прогноз',
    'main_menu':            'В главное меню',
    'check_another_date':   'Проверить другую дату',
    'change_forecast_time': '⌛Изменить время прогноза',
    'confirm':              'Подтверждаю ☑',
    'decline':              'Нет, вернуться назад ❎',
    'one_month':            '1 месяц | 400 рублей',
    'two_month':            '2 месяца | 750 рублей',
    'three_month':          '3 месяца | 1050 рублей',
    'six_month':            '6 месяцев | 2000 рублей',
    'twelve_month':         '12 месяцев | 3800 рублей',
    'yookassa':             'YooKassa'
}
bt = SimpleNamespace(**buttons_text) 


class KeyboardManager:
    def __init__(self, database: Database):
        self.database = database
        
        # Birth data
        self.start = self.build_keyboard_from_structure(
            [
                [bt.enter_birth_data, bt.enter_birth_data]
            ],
            is_inline=True
        )

        self.choose_time = self.build_keyboard_from_structure(
            [
                [bt.night, '1:00'],
                [bt.morning, '7:00'],
                [bt.day, '13:00'],
                [bt.evening, '19:00'],
                [bt.back]
            ],
            is_inline=True
        )

        # Main Menu
        self.main_menu = self.build_keyboard_from_structure(
            [
                [bt.subscription, bt.forecast],
                [bt.dreams, bt.card_of_the_day],
                [bt.general_forecasts, bt.moon_in_sign],
                [bt.change_timezone],
                [bt.tech_support]
            ]
        )

        # Predict
        self.predict_choose_action = self.build_keyboard_from_structure(
            [
                [bt.forecast_for_date],
                [bt.daily_forecast],
                [bt.main_menu]
            ]
        )
        self.predict_completed = self.build_keyboard_from_structure(
            [
                [bt.check_another_date],
                [bt.moon_in_sign, bt.general_forecasts],
                [bt.back]
            ]
        )
        self.every_day_prediction_activated = self.build_keyboard_from_structure(
            [
                [bt.change_forecast_time],
                [bt.back]
            ]
        )

        # Subscription
        self.subscription = self.build_keyboard_from_structure(
            [
                [
                    (bt.one_month, SubscriptionPeriod(months=1)),
                    (bt.two_month, SubscriptionPeriod(months=2))
                ],
                [
                    (bt.three_month, SubscriptionPeriod(months=3)),
                    (bt.six_month, SubscriptionPeriod(months=6))
                ],
                [
                    (bt.twelve_month, SubscriptionPeriod(months=12))
                ],
                [
                    (bt.back, bt.back)
                ]
            ],
            is_inline=True
        )
        self.payment_methods = self.build_keyboard_from_structure(
            [
                [
                    bt.yookassa
                ],
                [
                    bt.back
                ]
            ],
            is_inline=True
        )

        # No category
        self.confirm = self.build_keyboard_from_structure(
            [
                [bt.confirm],
                [bt.decline]
            ],
            is_inline=True
        )
        self.back = self.build_keyboard_from_structure(
            [
                [bt.back]
            ],
            is_inline=True
        )
        self.to_main_menu = self.build_keyboard_from_structure(
            [
                [bt.main_menu]
            ],
            is_inline=True
        )

        self.reply_back = self.build_keyboard_from_structure(
            [
                [bt.back]
            ]
        )


    def predict_choose_date(self, date: str) -> InlineKeyboardMarkup:
        markup: InlineKeyboardMarkup = self.build_keyboard_from_structure(
            [
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
                Exception(
                    'Чет несоответствие типов какое-то. Ты написал что тип реплай,'
                    f'а пихаешь туда не str, а {type(item)}'
                )

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
    
