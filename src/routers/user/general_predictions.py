from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.enums import GeneralPredictionType
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import MainMenu


r = Router()

DATE_FORMAT: str = config.get("database.date_format")
WEEK_FORMAT: str = "%G-W%V"
MONTH_FORMAT: str = config.get("database.month_format")

GENERAL_PREDICTION_IMAGE = config.get("files.general_prediction")

CALLBACK_DATA_TO_GENERAL_PREDICTION_TYPE = {
    bt.prediction_on_week: GeneralPredictionType.week,
    bt.prediction_on_day: GeneralPredictionType.day,
    bt.prediction_on_month: GeneralPredictionType.month
}
PRED_TYPE_TO_DATE_FMT = {
    GeneralPredictionType.day: DATE_FORMAT,
    GeneralPredictionType.month: MONTH_FORMAT,
    GeneralPredictionType.week: WEEK_FORMAT,
}


@r.callback_query(F.data == bt.general_predictions)
async def general_predictions_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await general_predictions_menu(callback.message, state, keyboards)


@r.message(F.text, F.text == bt.general_predictions)
async def general_predictions_menu(
    message: Message, 
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer_photo(
        photo=GENERAL_PREDICTION_IMAGE,
        caption=messages.USER_CHOOSE_GENERAL_PREDICTION_TYPE,
        reply_markup=keyboards.user_gen_pred_type,
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.general_predictions_get_type)


@r.callback_query(MainMenu.general_predictions_get_type)
async def get_prediction_type(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database,
):
    prediction_type = CALLBACK_DATA_TO_GENERAL_PREDICTION_TYPE[callback.data]
    format = PRED_TYPE_TO_DATE_FMT[prediction_type]

    date_str = datetime.now().strftime(format)
    print(f'{date_str = }')
    prediction_text = database.get_general_prediction(date_str)

    if prediction_text is None:
        prediction_text = messages.GENERAL_PREDICTION_NOT_ADDED

    await callback.message.answer_photo(
        photo=GENERAL_PREDICTION_IMAGE
    )
    bot_message = await callback.message.answer(
        text=prediction_text,
        reply_markup=keyboards.to_main_menu,
        parse_mode='html'
    )
    await state.update_data(delete_keyboard_message_id=bot_message.message_id)
    await state.set_state(MainMenu.end_action)
