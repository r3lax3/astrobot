from datetime import datetime
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.enums import GeneralPredictionType
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import AdminStates

r = Router()

ADMINS: List[int] = config.get("admins.ids")

DATETIME_FORMAT: str = config.get("database.datetime_format")
MONTH_FORMAT: str = config.get("database.month_format")
DATE_FORMAT: str = config.get("database.date_format")

WEEK_FORMAT: str = "%G-W%V"
FROM_WEEK_STR_FORMAT = "%G-W%V-%u"


CALLBACK_DATA_TO_GENERAL_PREDICTION_TYPE = {
    bt.prediction_on_week: GeneralPredictionType.week,
    bt.prediction_on_day: GeneralPredictionType.day,
    bt.prediction_on_month: GeneralPredictionType.month
}
GENERAL_PREDICTION_TYPE_TO_READABLE_TYPE = {
    GeneralPredictionType.day: "На день",
    GeneralPredictionType.month: "На месяц",
    GeneralPredictionType.week: "На неделю",
}
PRED_TYPE_TO_DATE_FMT = {
    GeneralPredictionType.day: DATE_FORMAT,
    GeneralPredictionType.month: MONTH_FORMAT,
    GeneralPredictionType.week: FROM_WEEK_STR_FORMAT,
}
PRED_TYPE_TO_EXAMPLE = {
    GeneralPredictionType.day: "19.10.2023",
    GeneralPredictionType.week: "2023-W45",
    GeneralPredictionType.month: "2023-03 или 2023-3",
}


@r.callback_query(AdminStates.get_general_prediction_date, F.data == bt.back)
@r.callback_query(AdminStates.choose_action, F.data == bt.general_predictions_add)
async def general_predictions_add_menu(
    callback: CallbackQuery, 
    state: FSMContext, 
    keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.CHOOSE_GENERAL_PREDICTION_TYPE,
        reply_markup=keyboards.choose_general_prediction_type,
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.choose_general_prediction_type)


@r.callback_query(AdminStates.choose_general_prediction_type)
async def get_general_prediction_date_menu(
    callback: CallbackQuery,
    state: FSMContext, 
    keyboards: KeyboardManager
):
    await state.update_data(
        general_predictions_type=CALLBACK_DATA_TO_GENERAL_PREDICTION_TYPE[callback.data].value
    )
    await enter_general_prediction_date(callback.message, state, keyboards)


@r.callback_query(AdminStates.get_general_prediction_text, F.data == bt.back)
async def enter_general_prediction_date_callback_handler(
    callback: CallbackQuery,
    state: FSMContext, 
    keyboards: KeyboardManager
):
    await enter_general_prediction_date(callback.message, state, keyboards)


async def enter_general_prediction_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    predictions_type = GeneralPredictionType(data["general_predictions_type"])

    bot_message = await message.answer(
        messages.ENTER_GENERAL_PREDICTION_DATE.format(
            type=GENERAL_PREDICTION_TYPE_TO_READABLE_TYPE[predictions_type], 
            format=PRED_TYPE_TO_EXAMPLE[predictions_type]
        ),
        reply_markup=keyboards.back,
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_general_prediction_date)


@r.message(AdminStates.get_general_prediction_date, F.text)
async def get_general_prediction_date(
    message: Message, 
    state: FSMContext,
    keyboards: KeyboardManager, 
    database
):
    data = await state.get_data()
    
    prediction_type = GeneralPredictionType(data["general_predictions_type"])
    prediction_format = PRED_TYPE_TO_DATE_FMT[prediction_type]

    try:
        # Need for iso format
        if prediction_type == GeneralPredictionType.week:
            text = message.text + "-1"
            format = FROM_WEEK_STR_FORMAT
            print(f'{text = }, {format = }')
            datetime.strptime(message.text + "-1", FROM_WEEK_STR_FORMAT)  
        else:
            datetime.strptime(message.text, prediction_format)

    except ValueError:
        bot_message1 = await message.answer(messages.GET_GENERAL_PREDICTION_DATE_ERROR)
        bot_message2 = await message.answer(
            messages.ENTER_GENERAL_PREDICTION_DATE.format(
                type=GENERAL_PREDICTION_TYPE_TO_READABLE_TYPE[prediction_type],
                format=PRED_TYPE_TO_EXAMPLE[prediction_type],
            ),
            reply_markup=keyboards.back,
        )
        await state.update_data(
            del_messages=[
                bot_message1.message_id, 
                bot_message2.message_id
            ]
        )

    else:

        if prediction_type == GeneralPredictionType.week:
            formatted_date = datetime.strptime(
                message.text + "-1", 
                FROM_WEEK_STR_FORMAT
            ).strftime(WEEK_FORMAT)
        else:
            formatted_date = datetime.strptime(
                message.text,
                prediction_format
            ).strftime(prediction_format)

        await state.update_data(general_prediction_date=formatted_date)
        await enter_general_prediction_text(message, state, keyboards, database)


async def enter_general_prediction_text(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager, 
    database
):
    data = await state.get_data()

    general_prediction = database.get_general_prediction(
        data["general_prediction_date"]
    )

    prediction_type = GeneralPredictionType(data["general_predictions_type"])


    if general_prediction is not None:
        bot_message = await message.answer(
            messages.ENTER_GENERAL_PREDICTION_TEXT_ALREADY_ADDED.format(
                type=data["general_predictions_type"],
                date=data["general_prediction_date"],
                text=general_prediction,
            ),
            reply_markup=keyboards.back,
        )
    else:
        bot_message = await message.answer(
            messages.ENTER_GENERAL_PREDICTION_TEXT.format(
                type=GENERAL_PREDICTION_TYPE_TO_READABLE_TYPE[prediction_type],
                date=data["general_prediction_date"],
            ),
            reply_markup=keyboards.back,
        )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_general_prediction_text)


@r.message(AdminStates.get_general_prediction_text, F.text)
async def get_general_prediction_text(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager, 
    database
):
    data = await state.get_data()

    prediction_type = GeneralPredictionType(data["general_predictions_type"])
    prediction_date = data["general_prediction_date"]

    database.add_general_prediction(date=prediction_date, prediction=message.html_text)

    bot_message = await message.answer(
        messages.GENERAL_PREDICTION_ADDED.format(
            type=GENERAL_PREDICTION_TYPE_TO_READABLE_TYPE[prediction_type],
            date=data["general_prediction_date"],
            text=message.html_text,
        ),
        reply_markup=keyboards.back_to_adminpanel,
        parse_mode="html",
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.action_end)

