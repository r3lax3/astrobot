from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src import config, messages
from src.routers.states import MainMenu
from src.keyboard_manager import KeyboardManager, bt
from src.database import Database


r = Router()
DATE_FORMAT: str = config.get('database.date_format')
WEEK_FORMAT: str = config.get('database.week_format')
MONTH_FORMAT: str = config.get('database.month_format')

GENERAL_PREDICTION_IMAGE = config.get('files.general_prediction')

pred_type_to_date_fmt = {
    bt.prediction_on_day: DATE_FORMAT,
    bt.prediction_on_week: WEEK_FORMAT,
    bt.prediction_on_month: MONTH_FORMAT
}


@r.callback_query(
    F.data == bt.general_predictions
)
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
    bot_message = await message.answer(
        messages.user_choose_general_prediction_type,
        reply_markup=keyboards.user_gen_pred_type
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.general_predictions_get_type)


@r.callback_query(MainMenu.general_predictions_get_type)
async def get_prediction_type(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    format = pred_type_to_date_fmt[callback.data]

    date_str = datetime.now().strftime(format)
    prediction_text = database.get_general_prediction(date_str)
    if prediction_text is None:
        prediction_text = messages.general_prediction_not_added
    
    bot_message = await callback.message.answer_photo(
        photo=GENERAL_PREDICTION_IMAGE,
        caption=prediction_text,
        reply_markup=keyboards.to_main_menu
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(MainMenu.end_action)

