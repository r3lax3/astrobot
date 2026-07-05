from types import SimpleNamespace
from typing import List, Tuple, Union

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)

from src.exceptions import InvalidButtonTypeException, TypeMismatchException
from src.models import DateModifier, SubscriptionPeriod

buttons_text: dict = {
    # Navigation
    "enter_birth_data": "Ввести данные рождения",
    "back": "🔙 Назад",
    "main_menu": "В главное меню",
    "back_to_menu": "Вернуться в меню",
    "back_to_adminpanel": "Назад в админ-панель",
    "decline": "Нет, вернуться назад ❎",
    "confirm": "Подтверждаю ☑",

    # Time of day
    "night": "Ночь",
    "morning": "Утро",
    "day": "День",
    "evening": "Вечер",

    # Predictions
    "prediction": "🔮Прогноз",
    "prediction_no_access": "🔓Прогноз",
    "prediction_for_date": "🕓 Прогноз на дату",
    "prediction_for_today": "Прогноз на сегодня",
    "daily_prediction": "⌚️ Ежедневный прогноз",
    "check_another_date": "Проверить другую дату",

    # Subscription
    "subscription": "🌟Подписка",
    "buy_subscription": "Купить подписку",
    "one_month": "1 месяц | 400 рублей",
    "two_month": "2 месяца | 750 рублей",
    "three_month": "3 месяца | 1050 рублей",
    "six_month": "6 месяцев | 2000 рублей",
    "twelve_month": "12 месяцев | 3800 рублей",
    "yookassa": "YooKassa",
    "offer": "Оффер",
    "redirect_button_text": "Оплатить подписку",
    "check_payment_status": "Проверить статус платежа",
    "use_this_promocode": "Использовать этот промокод",
    "enter_promocode": "Ввести промокод",
    "activate_promocode": "Активировать промокод",
    "try_in_deal": "Испытать в деле",

    # Profile settings
    "profile_settings": "⚙️Настройки профиля",
    "change_timezone": "✈️Смена часового пояса",
    "name": "✍️ Имя",
    "theme": "🌃 Тема",
    "gender": "👤 Пол",
    "male": "🙋‍♂️Мужчина",
    "female": "🙋‍♀️Женщина",

    # Card of day
    "card_of_day": "🃏Карта Дня",

    # Moon in sign
    "moon_in_sign": "🌗 Луна в знаке",
    "favorable": "🟢 Благоприятно",
    "unfavorable": "🔴 Неблагоприятно",
    "blank_moon": "🌒 Холостая луна",
    'general': "Общий",

    # General predictions
    "general_predictions": "🌒 Общие прогнозы",
    "prediction_on_day": "🗓️ Общий прогноз на день",
    "prediction_on_week": "📆 Общий прогноз на неделю",
    "prediction_on_month": "📅 Общий прогноз на месяц",

    # Admin
    "add_card_of_day": "Добавить карту дня",
    "user_settings": "Настройки пользователя",
    "delete_user_subscription": "Выключить подписку пользователя",
    "general_predictions_add": "Добавление Общих Прогнозов",
    "change_user_subscription_end": "Изменить дату окончания подписки",
    "statistics": "Статистика",
    "broadcast": "Рассылка",

    # Misc
    "dreams": "💫 Сны",
    "about_bot": "🤔 О боте",
    "support": "📞 Поддержка",
    "try_again": "Попробовать ещё раз",
    "compatibility": "💞Совместимость",
}
bt = SimpleNamespace(**buttons_text)

from_text_to_bt: dict = {v: k for k, v in buttons_text.items()}


class KeyboardManager:
    def __init__(self, database):
        self.database = database

        # Birth data

        self.enter_birth_data = self.build(
            [[bt.enter_birth_data]], is_inline=True
        )
        self.choose_time = self.build(
            [
                [(bt.night, "1:00"), (bt.morning, "7:00")],
                [(bt.day, "13:00"), (bt.evening, "19:00")],
                [bt.back],
            ],
            is_inline=True,
        )

        # User info

        self.get_gender = self.build(
            [
                [bt.male, bt.female],
                [bt.back]
            ],
            is_inline=True
        )

        # Main Menu

        self.main_menu = self.build(
            [
                [bt.subscription, bt.prediction],
                [bt.card_of_day],
                [bt.general_predictions, bt.moon_in_sign],
                [bt.compatibility, bt.dreams],
                [bt.profile_settings],
                [bt.about_bot, bt.support],
            ]
        )
        self.main_menu_prediction_no_access = self.build(
            [
                [bt.subscription, bt.prediction_no_access],
                [bt.card_of_day],
                [bt.general_predictions, bt.moon_in_sign],
                [bt.compatibility, bt.dreams],
                [bt.profile_settings],
                [bt.about_bot, bt.support],
            ]
        )

        # Prediction

        self.prediction_access_denied = self.build(
            [
                [bt.subscription],
                [bt.main_menu]
            ],
            is_inline=True
        )
        self.predict_choose_action = self.build(
            [
                [bt.prediction_for_date],
                [bt.daily_prediction],
                [bt.main_menu]
            ]
        )
        self.predict_completed = self.build(
            [
                [bt.check_another_date],
                [bt.moon_in_sign, bt.general_predictions],
                [bt.back],
            ],
            is_inline=True,
        )

        # Subscription

        self.buy_subscription = self.build(
            [
                [
                    (bt.one_month, SubscriptionPeriod(months=1)),
                    (bt.two_month, SubscriptionPeriod(months=2)),
                ],
                [
                    (bt.three_month, SubscriptionPeriod(months=3)),
                    (bt.six_month, SubscriptionPeriod(months=6)),
                ],
                [
                    (bt.twelve_month, SubscriptionPeriod(months=12))
                ],
                [bt.back_to_menu],
            ],
            is_inline=True,
        )
        self.payment_methods = self.build(
            [
                [bt.yookassa],
                [bt.back]
            ],
            is_inline=True
        )
        self.payment_success = self.build(
            [
                [bt.use_this_promocode],
                [bt.back_to_menu]
            ],
            is_inline=True
        )
        self.payment_canceled = self.build(
            [
                [bt.try_again],
                [bt.back_to_menu]
            ],
            is_inline=True
        )
        self.subscription = self.build(
            [
                [bt.buy_subscription, bt.enter_promocode],
                [bt.main_menu]
            ],
            is_inline=True
        )
        self.get_activate_promocode_confirm = self.build(
            [
                [bt.activate_promocode],
                [bt.back]
            ],
            is_inline=True
        )
        self.promocode_activated = self.build(
            [
                [bt.try_in_deal],
                [bt.back_to_menu]
            ],
            is_inline=True
        )

        # Compatibility

        self.gender_not_choosen = self.build(
            [
                [bt.profile_settings],
                [bt.main_menu]
            ], is_inline=True
        )

        # Profile Settings

        self.profile_settings = self.build(
            [
                [bt.change_timezone],
                [bt.gender, bt.name],
                [bt.theme],
                [bt.main_menu]
            ],
            is_inline=True,
        )
        self.choose_gender = self.build(
            [
                [bt.male, bt.female],
                [bt.back]
            ], is_inline=True
        )

        # General Predictions

        self.user_gen_pred_type = self.build(
            [
                [bt.prediction_on_day],
                [bt.prediction_on_week],
                [bt.prediction_on_month],
                [bt.main_menu],
            ],
            is_inline=True,
        )

        # Moon in sign

        self.moon_in_sign_menu = self.build(
            [
                [bt.blank_moon],
                [bt.favorable, bt.unfavorable],
                [bt.main_menu]
            ],
            is_inline=True,
        )

        # No category

        self.confirm = self.build(
            [
                [bt.confirm],
                [bt.decline]
            ], is_inline=True
        )
        self.back = self.build(
            [
                [bt.back]
            ],
            is_inline=True
        )
        self.to_main_menu = self.build(
            [
                [bt.main_menu]
            ],
            is_inline=True
        )

        self.reply_back = self.build(
            [
                [bt.back]
            ]
        )

        # ADMIN

        self.adminpanel = self.build(
            [
                [bt.general_predictions_add],
                [bt.user_settings],
                [bt.add_card_of_day],
                [bt.statistics],
                [bt.broadcast],
            ],
            is_inline=True,
        )
        self.choose_general_prediction_type = self.build(
            [
                [bt.prediction_on_day],
                [bt.prediction_on_week],
                [bt.prediction_on_month],
                [bt.back_to_adminpanel],
            ],
            is_inline=True,
        )
        self.back_to_adminpanel = self.build(
            [
                [bt.back_to_adminpanel]
            ], is_inline=True
        )
        self.user_info_menu = self.build(
            [
                [bt.change_user_subscription_end],
                [bt.back_to_adminpanel]
            ], is_inline=True
        )
        self.change_user_subscription_end = self.build(
            [
                [bt.delete_user_subscription],
                [bt.back_to_adminpanel]
            ], is_inline=True
        )

    def predict_choose_date(self, date: str) -> InlineKeyboardMarkup:
        return self.build(
            [
                [(date, "null")],
                [
                    ("+1", DateModifier(modifier=1)),
                    ("+5", DateModifier(modifier=5)),
                    ("+10", DateModifier(modifier=10)),
                    ("+30", DateModifier(modifier=30)),
                ],
                [
                    ("-1", DateModifier(modifier=-1)),
                    ("-5", DateModifier(modifier=-5)),
                    ("-10", DateModifier(modifier=-10)),
                    ("-30", DateModifier(modifier=-30)),
                ],
                [bt.confirm],
                [bt.decline],
            ],
            is_inline=True,
        )

    def payment_redirect(self, redirect_url: str):
        return self.build(
            [
                [
                    (bt.redirect_button_text, redirect_url)
                    # (bt.offer, offer_url)
                ],
                [bt.check_payment_status],
                [bt.back]
            ],
            is_inline=True
        )

    @staticmethod
    def pack_button(
        item: Union[str, Tuple[str, Union[str, CallbackData]]],
        is_inline: bool
    ):
        if is_inline:
            if isinstance(item, str):
                return InlineKeyboardButton(text=item, callback_data=item)
            if isinstance(item, tuple):
                if isinstance(item[1], str):
                    if item[1].startswith('https://'):
                        return InlineKeyboardButton(text=item[0], url=item[1])
                    return InlineKeyboardButton(text=item[0], callback_data=item[1])
                if isinstance(item[1], CallbackData):
                    return InlineKeyboardButton(
                        text=item[0], callback_data=item[1].pack()
                    )
            raise InvalidButtonTypeException(f'Wrong type of item: {item}')

        if isinstance(item, str):
            return KeyboardButton(text=item)

        raise TypeMismatchException(
            "Type mismatch detected. Expected a 'str' for non-inline "
            f"buttons, but received '{type(item).__name__}'."
        )

    def build(
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
