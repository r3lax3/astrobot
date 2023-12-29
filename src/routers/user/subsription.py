import uuid
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User
from yookassa import Configuration, Payment

from src import config, messages
from src.database import Database
from src.database.models import Payment as DBPayment
from src.database.models import Promocode
from src.enums import PromocodeStatus
from src.keyboard_manager import KeyboardManager, bt
from src.models import SubscriptionPeriod
from src.routers.states import MainMenu, Subscription

YOOKASSA_TOKEN: str = config.get("payments.yookassa_token")
YOOKASSA_SHOP_ID: int = config.get("payments.yookassa_shop_id")

DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")

BOT_USERNAME: str = config.get("bot.username")
OFFER_URL: str = config.get("payments.offer_url")

RETURN_URL = f"https://t.me/{BOT_USERNAME}"

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_TOKEN

MONTHS_TO_RUB_PRICE = {1: 400.00, 2: 750.00, 3: 1050.00, 6: 2000.00, 12: 3800.00}
MONTHS_TO_STR_MONTHS = {
    1: "1 месяц",
    2: "2 месяца",
    3: "3 месяца",
    6: "6 месяцев",
    12: "12 месяцев",
}

r = Router()


@r.callback_query(MainMenu.prediction_access_denied, F.data == bt.subscription)
@r.callback_query(Subscription.period, F.data == bt.back_to_menu)
@r.callback_query(Subscription.get_promocode, F.data == bt.back)
async def subscription_menu_callback_query_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    await subscription_menu(
        callback.message,
        state,
        keyboards,
    )


@r.message(F.text, F.text == bt.subscription)
async def subscription_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    bot_message = await message.answer(
        messages.subscrition_menu, reply_markup=keyboards.subscription
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.chooose_action)


# BUY SUBSCRIPTION
@r.callback_query(Subscription.payment_method, F.data == bt.back)
@r.callback_query(Subscription.payment_ended, F.data == bt.back_to_menu)
@r.callback_query(Subscription.chooose_action, F.data == bt.buy_subscription)
async def buy_subscription_menu(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
):
    data = await state.get_data()

    timezone_offset = timedelta(days=data["timezone_offset"])

    user = database.get_user(user_id=event_from_user.id)

    user_subscription_end_datetime = (
        datetime.strptime(user.subscription_end_date, DATETIME_FORMAT) + timezone_offset
    )
    now = datetime.utcnow()

    if now > user_subscription_end_datetime:
        bot_message = await callback.message.answer(
            messages.subscription_buy, reply_markup=keyboards.buy_subscription
        )
    else:
        subscription_end_datetime = (
            user_subscription_end_datetime + timezone_offset
        ).strftime(DATETIME_FORMAT)
        bot_message = await callback.message.answer(
            messages.subscription_check_and_buy.format(
                subscription_end_datetime=subscription_end_datetime
            ),
            reply_markup=keyboards.buy_subscription,
        )

    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.period)


@r.callback_query(Subscription.period)
async def get_choosed_period(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    months = SubscriptionPeriod.unpack(callback.data).months
    await state.update_data(months=months)
    await choose_payment_method(callback, state, keyboards)


@r.callback_query(Subscription.check_payment_status, F.data == bt.back)
async def choose_payment_method(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    bot_message = await callback.message.answer(
        messages.choose_payment_method, reply_markup=keyboards.payment_methods
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(Subscription.payment_method)


@r.callback_query(Subscription.payment_ended, F.data == bt.try_again)
@r.callback_query(Subscription.payment_method, F.data == bt.yookassa)
async def yookassa_payment(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
):
    data = await state.get_data()
    price = MONTHS_TO_RUB_PRICE[data["months"]]
    months_str = MONTHS_TO_STR_MONTHS[data["months"]]

    idempotence_key = str(uuid.uuid4())

    # Ниже я получаю дату автоматической отмены платежа,
    # которая должна быть спустя 6 часов после создания платежа
    now = datetime.utcnow()
    payment_auto_cancel_datetime = (now + timedelta(hours=6)).replace(
        microsecond=0
    ).isoformat() + "Z"

    payment = Payment.create(
        {
            "amount": {"value": f"{price}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": RETURN_URL},
            "capture": False,
            "expires_at": payment_auto_cancel_datetime,
            "description": f"Подписка на АстроПульс, {months_str}",
        },
        idempotence_key,
    )
    database.add_payment(
        DBPayment(
            payment_id=payment.id,
            user_id=event_from_user.id,
            status="pending",
            period=data["months"],
            created_at=datetime.utcnow().strftime(DATETIME_FORMAT),
        )
    )

    await state.update_data(
        redirect_url=payment.confirmation.confirmation_url, payment_id=payment.id
    )

    await get_payment_menu(callback.message, state, keyboards)


async def get_payment_menu(
    message: Message, state: FSMContext, keyboards: KeyboardManager
):
    data = await state.get_data()

    redirect_url = data["redirect_url"]

    bot_message = await message.answer(
        messages.payment_redirect,
        reply_markup=keyboards.payment_redirect(
            redirect_url=redirect_url, offer_url=OFFER_URL
        ),
    )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(Subscription.check_payment_status)


# CHECK PAYMENT STATUS
@r.callback_query(Subscription.check_payment_status, F.data == bt.check_payment_status)
async def check_payment_status(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    data = await state.get_data()
    payment_id = data["payment_id"]
    payment = Payment.find_one(payment_id)
    match payment.status:
        case "pending":
            bot_message = await callback.message.answer(messages.payment_pending)
            await get_payment_menu(bot_message, state, keyboards)
            return
        case "waiting_for_capture" | "paid":
            Payment.capture(payment_id)
            database.update_payment(
                payment_id=payment_id,
                status="success",
                status_change_timestamp=datetime.utcnow().strftime(DATETIME_FORMAT),
            )
            database.add_promocode(
                Promocode(
                    promocode=payment_id,
                    activated_by=None,
                    is_activated=False,
                    period=data["months"],
                )
            )
            await callback.message.answer(
                messages.your_promocode_is.format(promocode=payment_id)
            )
            payment_end_message = await callback.message.answer(
                messages.payment_succeess, reply_markup=keyboards.payment_succeess
            )
            await state.update_data(
                del_messages=[payment_end_message.message_id], promocode_str=payment_id
            )
        case _:  # 'canceled' or 'failed'. Or something else
            database.update_payment(
                payment_id=payment_id,
                status="failed",
                status_change_timestamp=datetime.utcnow().strftime(DATETIME_FORMAT),
            )
            payment_end_message = await callback.message.answer(
                messages.payment_check_error, reply_markup=keyboards.payment_canceled
            )
            await state.update_data(del_messages=[payment_end_message.message_id])
    await state.set_state(Subscription.payment_ended)


# PROMOCODE


# "ENTER PROMOCODE" MENU
@r.callback_query(Subscription.get_activate_promocode_confirm, F.data == bt.back)
@r.callback_query(Subscription.action_end, F.data == bt.back_to_menu)
@r.callback_query(Subscription.chooose_action, F.data == bt.enter_promocode)
async def enter_promocode_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext, keyboards: KeyboardManager
):
    await enter_promocode_menu(callback.message, state, keyboards)


async def enter_promocode_menu(
    message: Message, state: FSMContext, keyboards: KeyboardManager
):
    bot_message = await message.answer(
        messages.enter_promocode, reply_markup=keyboards.back
    )
    await state.update_data(del_messages=[bot_message.message_id, message.message_id])
    await state.set_state(Subscription.get_promocode)


# GET PROMOCODE
@r.message(Subscription.get_promocode, F.text)
async def get_promocode(
    message: Message, state: FSMContext, keyboards: KeyboardManager, database: Database
):
    await state.update_data(promocode_str=message.text)
    await enter_activate_promocode_confirm(message, state, keyboards, database)


@r.callback_query(Subscription.payment_ended, F.data == bt.use_this_promocode)
async def enter_activate_promocode_confirm_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
):
    await enter_activate_promocode_confirm(callback.message, state, keyboards, database)


async def enter_activate_promocode_confirm(
    message: Message, state: FSMContext, keyboards: KeyboardManager, database: Database
):
    data = await state.get_data()

    promocode_str = data.get("promocode_str", None)
    promocode = database.get_promocode(promocode_str)

    if promocode is not None:
        bot_message = await message.answer(
            messages.get_activate_promocode_confirm.format(
                promocode=promocode_str,
                period=MONTHS_TO_STR_MONTHS.get(promocode.period, "Ошибка"),
                status=(
                    PromocodeStatus.activated.value
                    if promocode.is_activated
                    else PromocodeStatus.not_activated.value
                ),
            ),
            reply_markup=keyboards.get_activate_promocode_confirm,
        )
        await state.update_data(
            del_messages=[bot_message.message_id],
            is_activated=promocode.is_activated,
            period=promocode.period,
        )
        await state.set_state(Subscription.get_activate_promocode_confirm)
    else:
        bot_message = await message.answer(messages.promocode_not_found)
        await enter_promocode_menu(bot_message, state, keyboards)


@r.message(Subscription.get_promocode)
async def get_promocode_error(
    message: Message, state: FSMContext, keyboards: KeyboardManager
):
    bot_message = await message.answer(messages.not_promocode)
    await enter_promocode_menu(bot_message, state, keyboards)


# GET PROMOCODE ACTIVATION CONFIRM
@r.callback_query(
    Subscription.get_activate_promocode_confirm, F.data == bt.activate_promocode
)
async def activate_promocode(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User,
):
    data = await state.get_data()

    promocode_str = data["promocode_str"]
    is_promocode_activated: bool = data["is_activated"]
    period = data["period"]

    if not is_promocode_activated:
        database.add_period_to_subscription_end_date(
            user_id=event_from_user.id, period=timedelta(days=period * 30)
        )
        database.update_promocode(
            promocode_str=promocode_str,
            is_activated=True,
            activated_by=event_from_user.id,
        )
        bot_message = await callback.message.answer(
            messages.promocode_activated, reply_markup=keyboards.promocode_activated
        )
        await state.update_data(
            del_messages=[bot_message.message_id], prediction_access=True
        )
        await state.set_state(Subscription.action_end)
    else:
        bot_message = await callback.message.answer(
            messages.promocode_already_activated, reply_markup=keyboards.back
        )
        await state.update_data(del_messages=[bot_message.message_id])
