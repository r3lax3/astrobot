from aiogram.fsm.state import State, StatesGroup


class GetBirthData(StatesGroup):
    date = State()
    time = State()
    location = State()
    confirm = State()


class ProfileSettings(StatesGroup):
    choose_option = State()

    get_current_location = State()
    location_confirm = State()

    choose_gender = State()

    get_new_name = State()


class MainMenu(StatesGroup):
    get_name = State()
    enter_birth_date = State()

    choose_action = State()

    prediction_access_denied = State()

    prediction_choose_action = State()
    prediction_choose_date = State()

    prediction_every_day_enter_time = State()

    prediction_end = State()

    general_predictions_get_type = State()

    moon_in_sign = State()

    end_action = State()


class Subscription(StatesGroup):
    chooose_action = State()

    period = State()
    payment_method = State()
    check_payment_status = State()
    payment_ended = State()

    get_promocode = State()
    get_activate_promocode_confirm = State()

    action_end = State()


class AdminStates(StatesGroup):
    choose_action = State()

    choose_general_prediction_type = State()
    get_general_prediction_date = State()
    get_general_prediction_text = State()

    get_user_message = State()
    user_info_menu = State()
    user_get_subscription_end_date = State()

    get_card_of_day = State()

    broadcast_get_message = State()
    broadcast_get_confirm = State()

    action_end = State()
