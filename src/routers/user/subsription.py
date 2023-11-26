import uuid

from datetime import datetime, timedelta

from yookassa import Configuration, Payment

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext

from src import config
from src.models import SubscriptionPeriod
from src.routers import messages
from src.routers.states import Subscription, MainMenu
from src.database import Database
from src.database.models import Payment as DBPayment
from src.keyboard_manager import KeyboardManager, bt


yookassa_token: str = config.get(
    'payments.yookassa_token'
)
yookassa_shop_id: int = config.get(
    'payments.yookassa_shop_id'
)

database_datetime_format: str = config.get(
    'database.datetime_format'
)
database_date_format: str = config.get(
    'database.date_format'
)

bot_username: str = config.get(
    'bot.username'
)
offer_url: str = config.get(
    'payments.offer_url'
)

return_url = f'https://t.me/{bot_username}'

Configuration.account_id = yookassa_shop_id
Configuration.secret_key = yookassa_token

months_to_rub_price = {
    1: 400.00,
    2: 750.00,
    3: 1050.00,
    6: 2000.00,
    12: 3800.00
}
months_to_str_months = {
    1: '1 месяц',
    2: '2 месяца',
    3: '3 месяца',
    6: '6 месяцев',
    12: '12 месяцев'
}

r = Router()


@r.callback_query(
    MainMenu.prediction_access_denied,
    F.data == bt.subscription
)
@r.callback_query(
    Subscription.payment_ended, 
    F.data == bt.back_to_menu
)
@r.callback_query(
    Subscription.payment_method, 
    F.data == bt.back
)
async def subscription_menu_callback_query_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await subscription_menu(
        callback.message, 
        state, 
        keyboards, 
        database,
        event_from_user
    )


@r.message(
    F.text,
    F.text == bt.subscription
)
async def subscription_menu(
    message: Message, 
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    data = await state.get_data()

    timezone_offset = timedelta(days=data['timezone_offset'])

    user = database.get_user(
        user_id=event_from_user.id
    )

    user_subscription_end_datetime = datetime.strptime(
        user.subscription_end_date, 
        database_datetime_format
    ) + timezone_offset 
    now = datetime.utcnow()

    if now > user_subscription_end_datetime:
        bot_message = await message.answer(
            messages.subscription_buy,
            reply_markup=keyboards.subscription
        )
    else:
        subscription_end_datetime = (
            (
                user_subscription_end_datetime + timezone_offset
            ).strftime(
                database_datetime_format
            )
        )

        bot_message = await message.answer(
            messages.subscription_check_and_buy.format(
                subscription_end_datetime=subscription_end_datetime
            ),
            reply_markup=keyboards.subscription
        )
    
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(Subscription.period)


@r.callback_query(Subscription.period)
async def get_choosed_period(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    months = SubscriptionPeriod.unpack(callback.data).months
    await state.update_data(months=months)
    await choose_payment_method(callback, state, keyboards)


@r.callback_query(
    Subscription.check_payment_status,
    F.data == bt.back
)
async def choose_payment_method(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.choose_payment_method,
        reply_markup=keyboards.payment_methods
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.payment_method)


@r.callback_query(
    Subscription.payment_ended, 
    F.data == bt.try_again
)
@r.callback_query(
    Subscription.payment_method,
    F.data == bt.yookassa
)
async def yookassa_payment(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    data = await state.get_data()
    price = months_to_rub_price[data['months']]
    months_str = months_to_str_months[data['months']]
    
    idempotence_key = str(uuid.uuid4())
    
    # Ниже я получаю дату автоматической отмены платежа, 
    # которая должна быть спустя 6 часов после создания платежа
    now = datetime.utcnow()
    payment_auto_cancel_datetime = (
        (
            now + timedelta(hours=6)
        ).replace(
            microsecond=0
        ).isoformat() + 'Z'
    )
    
    payment = Payment.create(
        {
            "amount": {
                "value": f"{price}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url 
            },
            "capture": 
                False,
            "expires_at": 
                payment_auto_cancel_datetime,
            "description": 
                f"Покупка/Продление подписки на АстроНавигатор, {months_str}"
        }, 
        idempotence_key
    )
    database.add_payment(
        DBPayment(
            payment_id=payment.id,
            user_id=event_from_user.id,
            status='pending',
            period=data['months'],
            created_at=datetime.utcnow().strftime(database_datetime_format)
        )
    )

    await state.update_data(
        redirect_url=payment.confirmation.confirmation_url,
        payment_id=payment.id
    )
    
    await get_payment_menu(callback.message, state, keyboards)


async def get_payment_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager
):
    data = await state.get_data()

    redirect_url = data['redirect_url']
    
    bot_message = await message.answer(
        messages.payment_redirect,
        reply_markup=keyboards.payment_redirect(
            redirect_url=redirect_url,
            offer_url=offer_url
        )
    )
    await state.update_data(
        del_messages=[
            bot_message.message_id, 
            message.message_id
        ]
    )
    await state.set_state(Subscription.check_payment_status)


@r.callback_query(
    Subscription.check_payment_status, 
    F.data == bt.check_payment_status
)
async def check_payment_status(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    data = await state.get_data()
    payment_id = data['payment_id']
    payment = Payment.find_one(payment_id)
    match payment.status:
        case 'pending':
            bot_message = await callback.message.answer(
                messages.payment_pending
            )
            await get_payment_menu(
                bot_message, 
                state,
                keyboards
            )
            return
        case 'waiting_for_capture' | 'paid':
            database.add_period_to_subscription_end_date(
                user_id=event_from_user.id, 
                period=timedelta(
                    days=data['months'] * 30
                )
            )
            Payment.capture(payment_id)
            database.update_payment(
                payment_id=payment_id, 
                status='success',
                ended_at=datetime.utcnow().strftime(database_datetime_format)
            )
            payment_end_message = await callback.message.answer(
                messages.payment_succeess,
                reply_markup=keyboards.payment_succeess
            )
            await state.update_data(
                prediction_access=True,
                subscription_end_date=True
            )
        case _:  # 'canceled' or 'failed'. Or something else
            database.update_payment(
                payment_id=payment_id, 
                status='failed',
                ended_at=datetime.utcnow().strftime(database_datetime_format)
            )
            payment_end_message = await callback.message.answer(
                messages.payment_check_error,
                reply_markup=keyboards.payment_canceled
            )
    await state.update_data(
        del_messages=[payment_end_message.message_id]
    )
    await state.set_state(Subscription.payment_ended)

