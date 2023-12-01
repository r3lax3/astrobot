from typing import List

from types import SimpleNamespace

from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters.callback_data import CallbackData

from src.database import Database
from src.models import DateModifier, SubscriptionPeriod


buttons_text: dict = {
    # Navigation
    'enter_birth_data': 'Ввести данные рождения',
    'back': '🔙 Назад',
    'main_menu': 'В главное меню',
    'back_to_menu': 'Вернуться в меню',
    'back_to_adminpanel': 'Назад в админ-панель',
    'decline': 'Нет, вернуться назад ❎',
    'confirm': 'Подтверждаю ☑',

    # Time of day
    'night': 'Ночь',
    'morning': 'Утро',
    'day': 'День',
    'evening': 'Вечер',

    # Predictions
    'prediction': '🔮Прогноз',
    'prediction_no_access': '🔓Прогноз',
    'prediction_for_date': '🕓 Прогноз на дату',
    'prediction_for_today': 'Прогноз на сегодня',
    'daily_prediction': '⌚️ Ежедневный прогноз',
    'check_another_date': 'Проверить другую дату',
    'change_prediction_time': '⌛Изменить время прогноза',

    # Subscription
    'subscription': '🌟Подписка',
    'buy_subscription': 'Купить подписку',
    'one_month': '1 месяц | 400 рублей',
    'two_month': '2 месяца | 750 рублей',
    'three_month': '3 месяца | 1050 рублей',
    'six_month': '6 месяцев | 2000 рублей',
    'twelve_month': '12 месяцев | 3800 рублей',
    'yookassa': 'YooKassa',
    'offer': 'Оффер',
    'redirect_button_text': 'Оплатить подписку',
    'check_payment_status': 'Проверить статус платежа',
    
    'use_this_promocode': 'Использовать этот промокод',
    'enter_promocode': 'Ввести промокод',
    'activate_promocode': 'Активировать промокод',
    'try_in_deal': 'Испытать в деле',
    
    # Profile settings
    'profile_settings': 'Настройки профиля',
    'change_timezone': '✈️Смена часового пояса',
    'name': '✍️ Имя',
    'theme': '🌃 Тема',
    'gender': '👤 Пол',
    'male': '🙋‍♂️Мужчина',
    'female': '🙋‍♀️Женщина',

    # Card of day
    'card_of_day': '🃏Карта Дня',

    # Moon in sign
    'moon_in_sign': '🌗 Луна в знаке',
    'favorable': '🟢 Благоприятно',
    'unfavorable': '🔴 Неблагоприятно',

    # General predictions
    'general_predictions': '🌒 Общие прогнозы',
    'prediction_on_day': 'На день',
    'prediction_on_week': 'На неделю',
    'prediction_on_month': 'На месяц',

    # Admin
    'add_card_of_day': 'Добавить карту дня',
    'user_settings': 'Настройки пользователя',
    'delete_user_subscription': 'Выключить подписку пользователя',
    'general_predictions_add': 'Добавление Общих Прогнозов',
    'change_user_subscription_end': 'Изменить дату окончания подписки',
    'statistics': "Статистика",

    # Misc
    'dreams': '💫 Сны',
    'about_bot': '🤔 О боте',
    'tech_support': '🔧 Техническая поддержка',
    'try_again': 'Попробовать ещё раз',
    'compatibility': 'Совместимость'
}
bt = SimpleNamespace(**buttons_text)

from_text_to_bt: dict = {
    v: k 
    for k, v in buttons_text.items()
}


class KeyboardManager:
    def __init__(self, database: Database):
        self.database = database
        
        # Birth data

        self.enter_birth_data = self.build_keyboard_from_structure(
            [
                [bt.enter_birth_data]
            ],
            is_inline=True
        )
        self.choose_time = self.build_keyboard_from_structure(
            [
                [(bt.night, '1:00')],
                [(bt.morning, '7:00')],
                [(bt.day, '13:00')],
                [(bt.evening, '19:00')],
                [bt.back]
            ],
            is_inline=True
        )

        # User info

        self.get_gender = self.build_keyboard_from_structure(
            [
                [bt.male, bt.female],
                [bt.back]
            ],
            is_inline=True
        )

        # Main Menu

        self.main_menu = self.build_keyboard_from_structure(
            [
                [bt.subscription, bt.prediction],
                [bt.card_of_day], # + bt.dreams
                [bt.general_predictions, bt.moon_in_sign],
                [bt.compatibility, bt.dreams], 
                [bt.profile_settings],
                [bt.about_bot, bt.tech_support]
            ]
        )
        self.main_menu_prediction_no_access = self.build_keyboard_from_structure(
            [
                [bt.subscription, bt.prediction_no_access],
                [bt.card_of_day], # + bt.dreams
                [bt.general_predictions, bt.moon_in_sign],
                [bt.compatibility, bt.dreams],
                [bt.profile_settings],
                [bt.about_bot, bt.tech_support]
            ]
        )

        # Prediction

        self.prediction_access_denied = self.build_keyboard_from_structure(
            [
                [bt.subscription],
                [bt.main_menu]
            ],
            is_inline=True
        )
        self.predict_choose_action = self.build_keyboard_from_structure(
            [
                [bt.prediction_for_date],
                [bt.daily_prediction],
                [bt.main_menu]
            ]
        )
        self.predict_completed = self.build_keyboard_from_structure(
            [
                [bt.check_another_date],
                [bt.moon_in_sign, bt.general_predictions],
                [bt.back]
            ],
            is_inline=True
        )
        self.every_day_prediction_activated = self.build_keyboard_from_structure(
            [
                [bt.change_prediction_time],
                [bt.back]
            ]
        )

        # Subscription
        
        self.buy_subscription = self.build_keyboard_from_structure(
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
                [bt.back_to_menu]
            ],
            is_inline=True
        )
        self.payment_methods = self.build_keyboard_from_structure(
            [
                [bt.yookassa],
                [bt.back]
            ],
            is_inline=True
        )
        self.payment_succeess = self.build_keyboard_from_structure(
            [
                [bt.use_this_promocode],
                [bt.back_to_menu]
            ],
            is_inline=True
        )
        self.payment_canceled = self.build_keyboard_from_structure(
            [
                [bt.try_again],
                [bt.back_to_menu]
            ],
            is_inline=True
        )
        self.subscription = self.build_keyboard_from_structure(
            [
                [bt.buy_subscription],
                [bt.enter_promocode]
            ],
            is_inline=True
        )
        self.get_activate_promocode_confirm = self.build_keyboard_from_structure(
            [
                [bt.activate_promocode],
                [bt.back]
            ],
            is_inline=True
        )
        self.promocode_activated = self.build_keyboard_from_structure(
            [
                [bt.try_in_deal],
                [bt.back_to_menu]
            ]
        )


        # Compatibility

        self.gender_not_choosen = self.build_keyboard_from_structure(
            [
                [bt.profile_settings],
                [bt.main_menu]
            ],
            is_inline=True
        )

        # Profile Settings

        self.profile_settings = self.build_keyboard_from_structure(
            [
                [bt.change_timezone],
                [bt.gender, bt.name],
                [bt.theme],
                [bt.main_menu]
            ],
            is_inline=True
        )
        self.choose_gender = self.build_keyboard_from_structure(
            [
                [bt.male, bt.female],
                [bt.back]
            ],
            is_inline=True
        )

        # General Predictions

        self.user_gen_pred_type = self.build_keyboard_from_structure(
            [
                [bt.prediction_on_day],
                [bt.prediction_on_week],
                [bt.prediction_on_month],
                [bt.main_menu]
            ],
            is_inline=True
        )

        # Moon in sign

        self.moon_in_sign_menu = self.build_keyboard_from_structure(
            [
                [bt.favorable, bt.unfavorable],
                [bt.main_menu]
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

        # ADMIN
        
        self.adminpanel = self.build_keyboard_from_structure(
            [
                [bt.general_predictions_add],
                [bt.user_settings],
                [bt.add_card_of_day],
                [bt.statistics]
            ],
            is_inline=True
        )
        self.choose_general_prediction_type = self.build_keyboard_from_structure(
            [
                [bt.prediction_on_day],
                [bt.prediction_on_week],
                [bt.prediction_on_month],
                [bt.back_to_adminpanel]
            ],
            is_inline=True
        )
        self.back_to_adminpanel = self.build_keyboard_from_structure(
            [
                [bt.back_to_adminpanel]
            ],
            is_inline=True
        )
        self.user_info_menu = self.build_keyboard_from_structure(
            [
                [bt.change_user_subscription_end],
                [bt.back_to_adminpanel]
            ],
            is_inline=True
        )
        self.change_user_subscription_end = self.build_keyboard_from_structure(
            [
                [bt.delete_user_subscription],
                [bt.back_to_adminpanel]
            ],
            is_inline=True
        )

    def predict_choose_date(self, date: str) -> InlineKeyboardMarkup:
        markup = self.build_keyboard_from_structure(
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
                [bt.confirm],
                [bt.decline]
            ],
            is_inline=True
        )
        return markup

    def payment_redirect(
        self, 
        redirect_url: str,
        offer_url: str
    ) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=bt.redirect_button_text,
                        url=redirect_url
                    ),
                    InlineKeyboardButton(
                        text=bt.offer, 
                        url=offer_url
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=bt.check_payment_status,
                        callback_data=bt.check_payment_status
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=bt.back, 
                        callback_data=bt.back
                    )
                ]
            ]
        )

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
            markup = InlineKeyboardMarkup(
                inline_keyboard=keyboard
            )
        else:
            markup = ReplyKeyboardMarkup(
                keyboard=keyboard, 
                resize_keyboard=True
            )
        
        return markup
    
