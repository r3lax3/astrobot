from aiogram.fsm.state import State, StatesGroup


class GetBirthData(StatesGroup):
    date = State()
    time = State()
    location = State()
    confirm = State()


class GetCurrentLocation(StatesGroup):
    location = State()
    confirm = State()


class GetCurrentLocationFirstTime(GetCurrentLocation):
    pass


class MainMenu(StatesGroup):
    choose_action = State()

    prediction_access_denied = State()

    prediction_choose_action = State()
    prediction_choose_date = State()

    predictin_every_day_choose_action = State()
    predictin_every_day_enter_time = State()

    prediction_end = State()

    end_action = State()


class Subscription(StatesGroup):
    period = State()
    payment_method = State()
    check_payment_status = State()
    payment_ended = State()

