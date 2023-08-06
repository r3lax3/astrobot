from aiogram.fsm.state import State, StatesGroup


class GetBirthData(StatesGroup):
    year = State()
    month = State()
    day = State()
    time = State()
    location = State()
    confirm = State()


class GetCurrentLocationFirstTime(StatesGroup):
    location = State()
    confirm = State()


class MainMenu(StatesGroup):
    choose_action = State()

    prediction_choose_action = State()
    prediction_choose_date = State()

    predictin_every_day_choose_action = State()
    predictin_every_day_enter_time = State()

    prediction_end = State()

    end_action = State()

