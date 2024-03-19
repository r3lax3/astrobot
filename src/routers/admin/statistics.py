from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


from src import config, messages
from src.database import crud, Session
from src.database.models import Payment, Promocode, User
from src.enums import Gender, PaymentStatus
from src.keyboards import keyboards, bt
from src.routers.states import AdminStates
from src.dicts import MONTHS_TO_RUB_PRICE


r = Router()
DATETIME_FORMAT: str = config.get("database.datetime_format")


@r.callback_query(F.data == bt.statistics)
async def statistics(callback: CallbackQuery, state: FSMContext):
    with Session() as session:
        users = crud.get_all_users(session)

        users_count = len(users)

        mens = len([user for user in users if user.gender == Gender.male])
        womens = len([user for user in users if user.gender == Gender.female])

        trial_users_count = 0
        active_clients_count = 0
        free_users_count = 0
        clients_count = 0

        ages = []

        now = datetime.utcnow()

        for user in users:
            end_date = datetime.strptime(
                user.subscription_end_date,
                DATETIME_FORMAT
            )
            payments = crud.get_payments(session, user_id=user.user_id)

            user_is_active_client = payments and now < end_date
            user_is_on_trial = not payments and now < end_date
            user_is_free = not payments and now > end_date
            user_is_client = bool(payments)

            if user_is_active_client:
                active_clients_count += 1
                clients_count += 1

            elif user_is_client:
                clients_count += 1

            elif user_is_on_trial:
                trial_users_count += 1

            elif user_is_free:
                free_users_count += 1

            birth_datetime = datetime.strptime(
                user.birth_datetime,
                DATETIME_FORMAT
            )
            ages.append((now - birth_datetime).days / 365)

        average_age = sum(ages) / len(ages)
        average_age_str = round(average_age, 1) if ages else "Нет данных"

        subscriptions = count_subscriptions(session)
        total_revenue = get_total_revenue(session)

        total_transactions = count_total_transactions(session)
        successful_transactions = count_successful_transactions(session)

        declined_transactions = total_transactions - successful_transactions

    text = messages.ADMIN_STATISTICS.format(
        users_count=users_count,
        trial_users_count=trial_users_count,
        clients_count=clients_count,
        active_clients_count=active_clients_count,
        free_users_count=free_users_count,
        average_age=average_age_str,
        percentage_men=mens,
        percentage_women=womens,
        subscription_1_month=subscriptions[1],
        subscription_2_month=subscriptions[2],
        subscription_3_month=subscriptions[3],
        subscription_6_month=subscriptions[6],
        subscription_1_year=subscriptions[12],
        total_transctions=total_transactions,
        successful_transactions=successful_transactions,
        declined_transactions=declined_transactions,
        total_revenue=total_revenue,
    )

    bot_message = await callback.message.answer(
        text,
        reply_markup=keyboards.back_to_adminpanel()
    )
    await state.update_data(del_messages=[bot_message.message_id])
    await state.set_state(AdminStates.action_end)


def count_all_users(database) -> int:
    return database.session.query(User).count()


def count_subscriptions(session: Session) -> dict:
    subscription_counts = {1: 0, 2: 0, 3: 0, 6: 0, 12: 0}
    # TODO
    # Переписать тут фильтрацию на платежи, а не на промокоды
    promocodes = session.query(Promocode).all()

    for promocode in promocodes:
        subscription_counts[promocode.period] += 1

    return subscription_counts


def get_total_revenue(session: Session) -> float:
    payments = crud.get_payments(session, status=PaymentStatus.SUCCESS.value)
    payments_prices = [
        float(payment.price)
        for payment in payments
        if payment.price
    ]

    return sum(payments_prices)


def count_total_transactions(session: Session) -> int:
    return session.query(Payment).filter(
        Payment.status != PaymentStatus.PENDING.value
    ).count()


def count_successful_transactions(session: Session) -> int:
    return session.query(Payment).filter(
        Payment.status == PaymentStatus.SUCCESS.value
    ).count()


def count_failed_transactions(session: Session) -> int:
    return session.query(Payment).filter(
        Payment.status == PaymentStatus.FAILED.value
    ).count()
