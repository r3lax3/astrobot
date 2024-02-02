from aiogram.filters.callback_data import CallbackData


class DateModifier(CallbackData, prefix="date_modifier"):
    modifier: int


class SubscriptionPeriod(CallbackData, prefix="sub_period"):
    months: int


class Payment(CallbackData, prefix='payment'):
    id: str


class Promocode(CallbackData, prefix='promocode'):
    promocode: str
