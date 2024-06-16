from datetime import datetime
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.database import crud, Session
from src.filters import IsDatetime
from src.keyboards import bt, keyboards
from src.routers.states import AdminStates


r = Router()

ADMINS: List[int] = config.get("admins.ids")
ADMIN_CHAT_ID: int = config.get("admin_chat.id")
ADMIN_CHAT_THREAD_CARDS_OF_DAY = config.get("admin_chat.threads.cards_of_day")

DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
WEEK_FORMAT: str = config.get("database.week_format")
MONTH_FORMAT: str = config.get("database.month_format")

PRED_TYPE_TO_DATE_FMT = {
    bt.prediction_on_day: DATE_FORMAT,
    bt.prediction_on_week: WEEK_FORMAT,
    bt.prediction_on_month: MONTH_FORMAT,
}

USER_ID_REGEX = r'\d+'


@r.callback_query(AdminStates.choose_action, F.data == bt.user_settings)
async def user_settings_menu(callback: CallbackQuery, state: FSMContext):
    bot_message = await callback.message.answer(
        messages.SEND_USER_MESSAGE_FOR_IDENTIFICATION,
        reply_markup=keyboards.back_to_adminpanel(),
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_user_message)


@r.message(AdminStates.get_user_message, F.forward_from)
@r.message(AdminStates.user_info_menu, F.forward_from)
async def get_user_message(message: Message, state: FSMContext):
    await state.update_data(user_id=message.forward_from.id)
    await get_user_info_menu(message, state)


@r.message(AdminStates.get_user_message, F.text.regexp(USER_ID_REGEX))
@r.message(AdminStates.user_info_menu, F.text.regexp(USER_ID_REGEX))
async def get_user_id_from_message(message: Message, state: FSMContext):
    await state.update_data(user_id=int(message.text))
    await get_user_info_menu(message, state)


@r.callback_query(
    AdminStates.user_get_subscription_end_date,
    F.data == bt.back
)
@r.callback_query(
    AdminStates.user_get_birth_datetime,
    F.data == bt.back
)
async def get_user_info_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext
):
    await get_user_info_menu(callback.message, state)


async def get_user_info_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id", 0)
    with Session() as session:
        user = crud.get_user(user_id=user_id)

        if user:
            unused_predictions = crud.get_unviewed_predictions_count(
                session,
                user_id=user_id
            )
            bot_message = await message.answer(
                messages.USER_INFO.format(
                    subscription_end=user.subscription_end_date,
                    birth_datetime=user.birth_datetime,
                    unused_predictions=unused_predictions,
                ),
                reply_markup=keyboards.user_info_menu(),
            )

        else:
            bot_message = await message.answer(
                messages.USER_NOT_FOUND,
                reply_markup=keyboards.back_to_adminpanel()
            )

    await state.update_data(
        del_messages=[bot_message.message_id],
        past_sub_end_date=user.subscription_end_date,
    )
    await state.set_state(AdminStates.user_info_menu)


@r.callback_query(
    AdminStates.user_info_menu,
    F.data == bt.change_user_subscription_end
)
async def change_user_subscription_end_menu(
    callback: CallbackQuery,
    state: FSMContext
):
    bot_message = await callback.message.answer(
        messages.ENTER_NEW_SUBSCRIPTION_END_DATE,
        reply_markup=keyboards.change_user_subscription_end(),
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.user_get_subscription_end_date)


@r.callback_query(
    AdminStates.user_get_subscription_end_date,
    F.data == bt.delete_user_subscription
)
async def delete_user_subscription(
    callback: CallbackQuery,
    state: FSMContext,
    scheduler,
):
    await state.update_data(
        new_subscription_end_date=datetime.utcnow().strftime(DATETIME_FORMAT)
    )
    await change_user_subscription_end_date(
        callback.message,
        state,
        scheduler
    )


@r.message(AdminStates.user_get_subscription_end_date, F.text, IsDatetime())
async def get_user_subscription_end_date(
    message: Message,
    state: FSMContext,
    scheduler,
):
    await state.update_data(new_subscription_end_date=message.text)
    await change_user_subscription_end_date(
        message,
        state,
        scheduler
    )


async def change_user_subscription_end_date(
    message: Message,
    state: FSMContext,
    scheduler,
):
    data = await state.get_data()
    user_id = data["user_id"]

    crud.update_subscription_end_date(
        user_id=user_id,
        date=datetime.strptime(
            data["new_subscription_end_date"],
            DATETIME_FORMAT
        )
    )

    await scheduler.set_all_jobs(user_id=user_id)

    await get_user_info_menu(message, state)


@r.callback_query(
    AdminStates.user_info_menu,
    F.data == bt.change_user_birth_datetime
)
async def change_user_birth_datetime_menu(
    callback: CallbackQuery,
    state: FSMContext
):
    bot_message = await callback.message.answer(
        messages.ENTER_USERS_NEW_BIRTH_DATETIME,
        reply_markup=keyboards.back(),
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.user_get_birth_datetime)


@r.message(AdminStates.user_get_birth_datetime, F.text, IsDatetime())
async def get_user_birth_datetime_date(
    message: Message,
    state: FSMContext,
):
    await state.update_data(new_user_birth_datetime=message.text)
    await change_user_birth_datetime(
        message,
        state
    )


async def change_user_birth_datetime(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    user_id = data["user_id"]
    new_user_birth_datetime = data["new_user_birth_datetime"]

    crud.update_user(
        user_id=user_id,
        birth_datetime=new_user_birth_datetime,
    )

    await get_user_info_menu(message, state)
