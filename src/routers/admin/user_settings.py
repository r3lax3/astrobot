from datetime import datetime
from typing import List

from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config, messages
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers.states import AdminStates
from src.filters import IsDatetime


r = Router()

admins: List[int] = config.get('admins.ids')
admin_chat_id: int = config.get(
    'admin_chat.id'
)
admin_chat_thread_cards_of_day = config.get(
    'admin_chat.threads.cards_of_day'
)
datetime_format: str = config.get('database.datetime_format')
date_format: str = config.get('database.date_format')
week_format: str = config.get('database.week_format')
month_format: str = config.get('database.month_format')

pred_type_to_date_fmt = {
    bt.prediction_on_day: date_format,
    bt.prediction_on_week: week_format,
    bt.prediction_on_month: month_format
}


@r.callback_query(
    AdminStates.choose_action,
    F.data == bt.user_settings
)
async def user_settings_menu(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.send_user_message_for_identification,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_user_message)


@r.message(AdminStates.get_user_message, F.forward_from)
async def get_user_message(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    await state.update_data(user_id=message.forward_from.id)
    await get_user_info_menu(message, state, keyboards, database)


@r.callback_query(
    AdminStates.user_get_subscription_end_date,
    F.data==bt.back
)
async def get_user_info_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):  
    await get_user_info_menu(
        callback.message, 
        state, 
        keyboards, 
        database
    )


async def get_user_info_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):  
    data = await state.get_data()
    user_id = data['user_id']
    user = database.get_user(user_id=user_id)
    if user:
        unused_predictions = database.get_unviewed_predictions_count(
            user_id=user_id
        )
        bot_message = await message.answer(
            messages.user_info.format(
                subscription_end=user.subscription_end_date,
                unused_predictions=unused_predictions
            ),
            reply_markup=keyboards.user_info_menu
        )
    else:
        bot_message = await message.answer(
            messages.user_not_found,
            reply_markup=keyboards.back_to_adminpanel
        )
    await state.update_data(
        del_messages=[bot_message.message_id],
        past_sub_end_date=user.subscription_end_date
    )
    await state.set_state(AdminStates.user_info_menu)


@r.callback_query(
    AdminStates.user_info_menu, 
    F.data==bt.change_user_subscription_end
)
async def change_user_subscription_end_menu(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.enter_new_subscription_end_date,
        reply_markup=keyboards.change_user_subscription_end
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(
        AdminStates.user_get_subscription_end_date
    )


@r.callback_query(
    AdminStates.user_get_subscription_end_date,
    F.data == bt.delete_user_subscription
)
async def delete_user_subscription(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    scheduler,
    bot: Bot
):
    await state.update_data(
        new_subscription_end_date=datetime.utcnow().strftime(datetime_format)
    )
    await change_user_subscription_end_date(
        callback.message, 
        state, 
        keyboards, 
        database,
        scheduler,
        bot
    )


@r.message(
    AdminStates.user_get_subscription_end_date, 
    F.text, 
    IsDatetime()
)
async def get_user_subscription_end_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    scheduler,
    bot: Bot

):
    await state.update_data(
        new_subscription_end_date=message.text
    )
    await change_user_subscription_end_date(
        message, 
        state, 
        keyboards, 
        database,
        scheduler,
        bot
    )

async def change_user_subscription_end_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    scheduler,
    bot: Bot
):
    data = await state.get_data()

    database.update_subscription_end_date(
        user_id=data['user_id'],
        date=datetime.strptime(
            data['new_subscription_end_date'], 
            datetime_format
        ) 
    )
    await scheduler.edit_send_message_job(
        user_id=data['user_id'],
        database=database,
        bot=bot
    )
    user = database.get_user(user_id=data['user_id'])

    bot_message = await message.answer(
        messages.changed_subscription_end_date.format(
            past_sub_end_date=data['past_sub_end_date'],
            changed_date=user.subscription_end_date,
            unused_predictions=database.get_unviewed_predictions_count(
                user_id=data['user_id']
            )
        ),
        reply_markup=keyboards.user_info_menu
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(
        AdminStates.user_info_menu
     )


