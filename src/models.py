from aiogram.filters.callback_data import CallbackData


class DateModifier(CallbackData, prefix="date_modifier"):
    modifier: int


class SubscriptionPeriod(CallbackData, prefix="sub_period"):
    months: int
