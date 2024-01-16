from datetime import datetime
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import AdminStates

r = Router()

admins: List[int] = config.get("admins.ids")

admin_chat_id: int = config.get("admin_chat.id")
admin_chat_thread_cards_of_day = config.get("admin_chat.threads.cards_of_day")

datetime_format: str = config.get("database.datetime_format")
date_format: str = config.get("database.date_format")
week_format: str = config.get("database.week_format")
month_format: str = config.get("database.month_format")

pred_type_to_date_fmt = {
    bt.prediction_on_day: date_format,
    bt.prediction_on_week: week_format,
    bt.prediction_on_month: month_format,
}
pred_type_to_example = {
    bt.prediction_on_day: "19.10.2023",
    bt.prediction_on_week: "2023-W45",
    bt.prediction_on_month: "2023-03 или 2023-3",
}


@r.callback_query(AdminStates.get_general_prediction_date, F.data == bt.back)
@r.callback_query(AdminStates.choose_action, F.data == bt.general_predictions_add)
async def general_predictions_add_menu(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.choose_general_prediction_type,
        reply_markup=keyboards.choose_general_prediction_type,
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.choose_general_prediction_type)


@r.callback_query(AdminStates.choose_general_prediction_type)
async def get_general_prediction_date_menu(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    await state.update_data(general_predictions_type=callback.data)
    await enter_general_prediction_date(callback.message, state, keyboards)


@r.callback_query(AdminStates.get_general_prediction_text, F.data == bt.back)
async def enter_general_prediction_date_callback_handler(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    await enter_general_prediction_date(callback.message, state, keyboards)


async def enter_general_prediction_date(
    message: Message, state: FSMContext, keyboards: KeyboardManager
):
    data = await state.get_data()

    predictions_type = data["general_predictions_type"]

    bot_message = await message.answer(
        messages.enter_general_prediction_date.format(
            type=predictions_type, 
            format=pred_type_to_example[predictions_type]
        ),
        reply_markup=keyboards.back,
    )
    await state.update_data(
        del_messages=[bot_message.message_id],
    )
    await state.set_state(AdminStates.get_general_prediction_date)


@r.message(AdminStates.get_general_prediction_date, F.text)
async def get_general_prediction_date(
    message: Message, 
    state: FSMContext,
    keyboards: KeyboardManager, 
    database: Database
):
    data = await state.get_data()
    prediction_type = data["general_predictions_type"]

    try:
        datetime.strptime(message.text, pred_type_to_date_fmt[prediction_type])

    except ValueError:
        bot_message1 = await message.answer(messages.get_general_prediction_date_error)
        bot_message2 = await message.answer(
            messages.enter_general_prediction_date.format(
                type=prediction_type,
                format=pred_type_to_example[prediction_type],
            ),
            reply_markup=keyboards.back,
        )
        await state.update_data(
            del_messages=[bot_message1.message_id, bot_message2.message_id]
        )

    else:
        prediction_format = pred_type_to_date_fmt[prediction_type]
        formatted_date = datetime.strptime(message.text, prediction_format).strftime(prediction_format)

        await state.update_data(general_prediction_date=formatted_date)
        await enter_general_prediction_text(message, state, keyboards, database)


async def enter_general_prediction_text(
    message: Message, 
    state: FSMContext, 
    keyboards: KeyboardManager,
    database: Database
):
    data = await state.get_data()

    general_prediction = database.get_general_prediction(
        data["general_prediction_date"]
    )

    if general_prediction is not None:
        bot_message = await message.answer(
            messages.enter_general_prediction_text.format(
                type=data["general_predictions_type"],
                date=data["general_prediction_date"],
                text=general_prediction,
            ),
            reply_markup=keyboards.back,
        )
    else:
        bot_message = await message.answer(
            messages.enter_general_prediction_text.format(
                type=data["general_predictions_type"],
                date=data["general_prediction_date"],
            ),
            reply_markup=keyboards.back,
        )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_general_prediction_text)


@r.message(AdminStates.get_general_prediction_text, F.text)
async def get_general_prediction_text(
    message: Message, state: FSMContext, keyboards: KeyboardManager, database: Database
):
    data = await state.get_data()

    prediction_type = data['general_predictions_type']
    prediction_date = data["general_prediction_date"]


    database.add_general_prediction(
        date=prediction_date, 
        prediction=message.html_text
    )

    bot_message = await message.answer(
        messages.general_prediction_added.format(
            type=prediction_type,
            date=data["general_prediction_date"],
            text=message.html_text,
        ),
        reply_markup=keyboards.back_to_adminpanel,
        parse_mode='html'
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.action_end)
