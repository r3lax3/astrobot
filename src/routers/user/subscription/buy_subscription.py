from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from src import config, messages
from src.keyboards import bt, keyboards
from src.database import crud
from src.database.models import Payment as DBPayment
from src.enums import PaymentMethod
from src.models import SubscriptionPeriod, SubscriptionItem
from src.routers.states import Subscription
from src.translations import (
    FROM_BT_TO_PAYMENT_METHOD,
    FROM_PAYMENT_METHOD_TO_PAYMENT_SERVICE
)
from .utils import get_subscription_status_text


DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")

BOT_USERNAME = config.get("bot.username")

PROMOCODE_IMAGE: str = config.get("files.promocode")

r = Router()


# BUY SUBSCRIPTION
@r.callback_query(Subscription.payment_method, F.data == bt.back)
@r.callback_query(Subscription.payment_ended, F.data == bt.back_to_menu)
@r.callback_query(F.data == bt.buy_subscription)
@r.callback_query(F.data == bt.renew_subscription)
async def buy_subscription_menu(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User,
):
    user = crud.get_user(user_id=event_from_user.id)
    subscription_status_text = get_subscription_status_text(user)

    bot_message = await callback.message.answer(
        messages.SUBSCRIPTION_CHECK_AND_BUY.format(
            subscription_status=subscription_status_text
        ),
        reply_markup=keyboards.buy_subscription()
    )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.period)


@r.callback_query(Subscription.period)
async def get_choosed_period(callback: CallbackQuery, state: FSMContext):
    months = SubscriptionPeriod.unpack(callback.data).months
    await state.update_data(months=months)
    await choose_payment_method(callback, state)


@r.callback_query(Subscription.check_payment_status, F.data == bt.back)
async def choose_payment_method(callback: CallbackQuery, state: FSMContext):
    bot_message = await callback.message.answer(
        messages.CHOOSE_PAYMENT_METHOD,
        reply_markup=keyboards.payment_methods()
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.payment_method)


@r.callback_query(
    Subscription.payment_method,
    F.data.in_([bt.yookassa, bt.prodamus])
)
async def get_payment_method(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User,
):
    if callback.data == bt.yookassa:
        await callback.message.answer(
            messages.THIS_PAYMENT_METHOD_NOT_WORK
        )

    await state.update_data(
        payment_method=FROM_BT_TO_PAYMENT_METHOD[callback.data].value
    )
    await create_payment(callback, state, event_from_user)


@r.callback_query(Subscription.payment_ended, F.data == bt.try_again)
async def create_payment(
    callback: CallbackQuery,
    state: FSMContext,
    event_from_user: User,
):
    data = await state.get_data()

    payment_method = PaymentMethod(data['payment_method'])
    payment_service = FROM_PAYMENT_METHOD_TO_PAYMENT_SERVICE[payment_method]

    months = data['months']

    payment = await payment_service.create_payment(months, event_from_user.id)
    crud.add_payment(
        DBPayment(
            payment_id=payment.id,
            user_id=event_from_user.id,
            status="pending",
            created_at=datetime.utcnow().strftime(DATETIME_FORMAT),
            item=SubscriptionItem(months=months).pack(),
            price=payment.price
        )
    )

    await state.update_data(
        payment_id=payment.id,
        redirect_url=payment.payment_link
    )

    await get_payment_menu(callback.message, state)


async def get_payment_menu(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    redirect_url = data['redirect_url']

    bot_message = await message.answer(
        messages.PAYMENT_REDIRECT,
        reply_markup=keyboards.payment_redirect(redirect_url)
    )
    await state.update_data(
        del_messages=[bot_message.message_id, message.message_id]
    )
    await state.set_state(Subscription.check_payment_status)
