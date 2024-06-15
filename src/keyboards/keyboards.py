from typing import Optional

from src import config
from src.utils import split_list
from src.models import DateModifier

from .callback_data import SubscriptionPeriod, Payment, Promocode
from .builder import KeyboardBuilder
from .buttons import bt


OFFER_URL = config.get("payments.offer_url")


# Birth data
def enter_birth_data():
    return KeyboardBuilder.build(
        [[bt.enter_birth_data]],
        is_inline=True
    )


def choose_time():
    return KeyboardBuilder.build(
        [
            [(bt.night, "1:00"), (bt.morning, "7:00")],
            [(bt.day, "13:00"), (bt.evening, "19:00")],
            [bt.back],
        ],
        is_inline=True,
    )


# User info
def get_gender():
    return KeyboardBuilder.build(
        [
            [bt.male, bt.female],
            [bt.back]
        ],
        is_inline=True
    )


# Main Menu
def main_menu(prediction_access: bool = True):
    return KeyboardBuilder.build(
        [
            [
                bt.subscription,
                bt.prediction if prediction_access else bt.prediction_no_access
            ],
            [bt.card_of_day],
            [bt.general_predictions, bt.moon_in_sign],
            [bt.compatibility, bt.dreams],
            [bt.profile_settings],
            [bt.about_bot, bt.support],
        ]
    )


# Prediction
def prediction_access_denied():
    return KeyboardBuilder.build(
        [
            [bt.subscription],
            [bt.main_menu]
        ],
        is_inline=True
    )


def predict_choose_action():
    return KeyboardBuilder.build(
        [
            [bt.prediction_for_date],
            [bt.daily_prediction],
            [bt.day_selection],
            [bt.main_menu]
        ]
    )


def predict_completed():
    return KeyboardBuilder.build(
        [
            [bt.check_another_date],
            [bt.moon_in_sign, bt.general_predictions],
            [bt.back],
        ],
        is_inline=True,
    )


# Subscription
def buy_subscription():
    return KeyboardBuilder.build(
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


def payment_methods():
    return KeyboardBuilder.build(
        [
            [bt.prodamus],  # , bt.yookassa],
            [bt.back]
        ],
        is_inline=True
    )


def payment_success(promocode: str):
    return KeyboardBuilder.build(
        [
            [(bt.use_this_promocode, Promocode(promocode=promocode))],
            [bt.main_menu]
        ],
        is_inline=True
    )


def payment_canceled():
    return KeyboardBuilder.build(
        [
            [bt.try_again],
            [bt.back_to_menu]
        ],
        is_inline=True
    )


def subscription_menu():
    return KeyboardBuilder.build(
        [
            [bt.buy_subscription, bt.enter_promocode],
            [bt.main_menu]
        ],
        is_inline=True
    )


def get_activate_promocode_confirm():
    return KeyboardBuilder.build(
        [
            [bt.activate_promocode],
            [bt.back]
        ],
        is_inline=True
    )


def promocode_activated():
    return KeyboardBuilder.build(
        [
            [bt.try_in_deal],
            [bt.back_to_menu]
        ],
        is_inline=True
    )


# Compatibility
def gender_not_choosen():
    return KeyboardBuilder.build(
        [
            [bt.profile_settings],
            [bt.main_menu]
        ],
        is_inline=True
    )


# Profile Settings
def profile_settings():
    return KeyboardBuilder.build(
        [
            [bt.change_timezone],
            [bt.gender, bt.name],
            [bt.theme],
            [bt.main_menu]
        ],
        is_inline=True,
    )


def choose_gender():
    return KeyboardBuilder.build(
        [
            [bt.male, bt.female],
            [bt.back]
        ],
        is_inline=True
    )


# General Predictions
def user_gen_pred_type():
    return KeyboardBuilder.build(
        [
            # [bt.prediction_on_day],
            [bt.prediction_on_week],
            [bt.prediction_on_month],
            [bt.main_menu],
        ],
        is_inline=True,
    )


# Moon in sign
def moon_in_sign_menu():
    return KeyboardBuilder.build(
        [
            [bt.blank_moon],
            [bt.favorable, bt.unfavorable],
            [bt.main_menu]
        ],
        is_inline=True,
    )


# No category
def confirm():
    return KeyboardBuilder.build(
        [
            [bt.confirm],
            [bt.decline]
        ],
        is_inline=True
    )


def back():
    return KeyboardBuilder.build(
        [
            [bt.back]
        ],
        is_inline=True
    )


def to_main_menu():
    return KeyboardBuilder.build(
        [
            [bt.main_menu]
        ],
        is_inline=True
    )


def reply_back():
    return KeyboardBuilder.build(
        [
            [bt.back]
        ]
    )


# ADMIN
def adminpanel():
    return KeyboardBuilder.build(
        [
            [bt.general_predictions_add],
            [bt.user_settings],
            [bt.add_card_of_day],
            [bt.statistics],
            [bt.broadcast],
        ],
        is_inline=True,
    )


def choose_general_prediction_type():
    return KeyboardBuilder.build(
        [
            # [bt.prediction_on_day],
            [bt.prediction_on_week],
            [bt.prediction_on_month],
            [bt.back_to_adminpanel],
        ],
        is_inline=True,
    )


def back_to_adminpanel():
    return KeyboardBuilder.build(
        [
            [bt.back_to_adminpanel]
        ],
        is_inline=True
    )


def user_info_menu():
    return KeyboardBuilder.build(
        [
            [bt.change_user_subscription_end],
            [bt.back_to_adminpanel]
        ],
        is_inline=True
    )


def change_user_subscription_end():
    return KeyboardBuilder.build(
        [
            [bt.delete_user_subscription],
            [bt.back_to_adminpanel]
        ],
        is_inline=True
    )


def payment_redirect(redirect_url: str):
    return KeyboardBuilder.build(
        [
            [
                (bt.redirect_button_text, redirect_url),
                (bt.offer, OFFER_URL)
            ],
            [bt.back]
        ],
        is_inline=True
    )


def day_selection_categories(categories: list[str]):
    return KeyboardBuilder.build(
        split_list(categories, 2) + [[bt.main_menu]],
        is_inline=True
    )


def day_selection_actions(actions: list[str]):
    return KeyboardBuilder.build(
        split_list(actions, 1) + [[bt.main_menu]],
        is_inline=True
    )


def predict_choose_date(date: str):
    return KeyboardBuilder.build(
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


def day_selection_success():
    return KeyboardBuilder.build(
        [
            [bt.renew_subscription, bt.choose_another_action],
            [bt.main_menu]
        ],
        is_inline=True
    )


def day_selection_failed():
    return KeyboardBuilder.build(
        [
            [bt.renew_subscription, bt.choose_another_action],
            [bt.main_menu]
        ],
        is_inline=True
    )


def day_selection_no_access():
    return KeyboardBuilder.build(
        [
            [bt.buy_subscription],
            [bt.main_menu]
        ],
        is_inline=True
    )
