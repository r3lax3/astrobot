from datetime import datetime
from typing import List

from aiogram import F, Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src import config
from src.database import Database
from src.keyboard_manager import KeyboardManager, bt
from src.routers import messages
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


@r.message(
    Command(commands=['admin']),
    F.from_user.id.in_(admins)
)
async def adminpanel(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.admin_menu,
        reply_markup=keyboards.adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.choose_action)

@r.callback_query(
    AdminStates.get_general_prediction_date,
    F.data == bt.back
)
@r.callback_query(
    F.from_user.id.in_(admins),
    F.data == bt.back_to_adminpanel
)
async def adminpane_callback_query_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await adminpanel(callback.message, state, keyboards)


@r.callback_query(
    AdminStates.get_general_prediction_date,
    F.data == bt.back
)
@r.callback_query(
    AdminStates.choose_action, 
    F.data == bt.general_predictions_add
)
async def general_predictions_add_menu(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.choose_general_prediction_type,
        reply_markup=keyboards.choose_general_prediction_type
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(
        AdminStates.choose_general_prediction_type
    )


@r.callback_query(
    AdminStates.choose_general_prediction_type
)
async def get_general_prediction_date_menu(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    await state.update_data(general_predictions_type=callback.data)
    await enter_general_prediction_date(
        callback.message, 
        state, 
        keyboards
    )


async def enter_general_prediction_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()
    
    bot_message = await message.answer(
        messages.enter_general_prediction_date.format(
            type=data['general_predictions_type']
        ),
        reply_markup=keyboards.back
    )
    await state.update_data(
        del_messages=[bot_message.message_id],
    )
    await state.set_state(AdminStates.get_general_prediction_date)


@r.message(
    AdminStates.get_general_prediction_date, 
    F.text
)
async def get_general_prediction_date(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    try:
        data = await state.get_data()

        datetime.strptime(
            message.text,
            pred_type_to_date_fmt[data['general_predictions_type']]
        )

        await state.update_data(
            general_prediction_date=message.text
        )
        await enter_general_prediction_text(
            message,
            state,
            keyboards,
            database
        )
    except ValueError:
        await get_general_prediction_date_error_hendler(
            message, 
            state, 
            keyboards
        )


@r.message(AdminStates.get_general_prediction_date)
async def get_general_prediction_date_error_hendler(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    bot_message = await message.answer(
        messages.enter_general_prediction_text.format(
            type=data['general_predictions_type']
        ),
        reply_markup=keyboards.back
    )
    await state.update_data(
        del_messages=[bot_message.message_id],
    )


async def enter_general_prediction_text(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    data = await state.get_data()

    general_prediction = database.get_general_prediction(
        data['general_prediction_date']
    )
    
    if general_prediction is not None:
        bot_message = await message.answer(
            messages.enter_general_prediction_text.format(
                type=data['general_predictions_type'],
                date=data['general_prediction_date'],
                text=general_prediction
            ),
            reply_markup=keyboards.back
        )
    else:
        bot_message = await message.answer(
            messages.enter_general_prediction_text.format(
                type=data['general_predictions_type'],
                date=data['general_prediction_date']
            ),
            reply_markup=keyboards.back
        )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_general_prediction_text)


@r.message(AdminStates.get_general_prediction_text, F.text)
async def get_general_prediction_text(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):
    data = await state.get_data()

    database.add_general_prediction(
        date=data['general_prediction_date'],
        prediction=message.text
    )

    bot_message = await message.answer(
        messages.general_prediction_added.format(
            type=data['general_predictions_type'],
            date=data['general_prediction_date'],
            text=message.text
        ),
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.action_ended)


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
    await get_user_info_menu(callback.message, state, keyboards, database)


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

@r.callback_query(
    AdminStates.choose_action,
    F.data == bt.add_card_of_day
)
async def add_card_of_day(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    bot_message = await callback.message.answer(
        messages.send_me_card,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.get_card_of_day)


@r.message(
    AdminStates.get_card_of_day,
    F.photo,
    F.media_group_id is None
)
async def get_card_of_day(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    image_resend_message = await message.copy_to(
        chat_id=admin_chat_id,
        message_thread_id=admin_chat_thread_cards_of_day
    )

    database.add_card_of_day(
        message_id=image_resend_message.message_id
    )

    bot_message = await message.answer(
        messages.card_of_day_successful_saved,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(del_messages=[bot_message.message_id])
