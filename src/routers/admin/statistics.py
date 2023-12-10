from typing import Tuple
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src import config, messages
from src.keyboard_manager import KeyboardManager, bt
from src.database import Database
from src.database.models import User, Payment
from src.routers.states import AdminStates


r = Router()
months_to_rub_price = {
    1: 400.00,
    2: 750.00,
    3: 1050.00,
    6: 2000.00,
    12: 3800.00
}

# "%d.%m.%Y %H:%M" at default
database_datetime_format: str = config.get(
    'database.datetime_format'
)


@r.callback_query(F.data == bt.statistics)
async def statistics(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database
):

    all_users = count_all_users(database)
    clients = count_clients(database)

    percentage_men, percentage_women = gender_percentage(database)

    trial_users = 0
    active_clients = 0
    free_users = 0

    ages = []

    now = datetime.utcnow()
    
    # Кусок кода вынесен сюда ради оптимизации
    users = database.session.query(User).all()

    for user in users:
        end_date = datetime.strptime(
            user.subscription_end_date,
            database_datetime_format
        )
        payments = database.get_payments(user_id=user.user_id)

        # Подсчет активных клиентов
        if payments and now < end_date:
            active_clients += 1

        elif not payments and now < end_date:
            trial_users += 1

        # Подсчет "бесплатников"
        elif not payments and now > end_date:
            free_users += 1

        birth_datetime = datetime.strptime(
            user.birth_datetime,
            database_datetime_format
        )
        ages.append((now - birth_datetime).days / 365)
    average_age = int(sum(ages) / len(ages)) if ages else 0

    subscriptions = count_subscriptions(database)
    total_revenue_val = total_revenue(database)

    total_transactions = count_total_transactions(database)
    successful_transactions = count_successful_transactions(database)
    declined_transactions = total_transactions - successful_transactions

    text = messages.admin_statistics.format(
        all_users=all_users,
        trial_users=trial_users,
        clients=clients,
        active_clients=active_clients,
        free_users=free_users,
        average_age=average_age,
        percentage_men=percentage_men,
        percentage_women=percentage_women,
        subscription_1_month=subscriptions[1],
        subscription_2_month=subscriptions[2],
        subscription_3_month=subscriptions[3],
        subscription_6_month=subscriptions[6],
        subscription_1_year=subscriptions[12],
        total_transctions=total_transactions,
        successful_transactions=successful_transactions,
        declined_transactions=declined_transactions,
        total_revenue=total_revenue_val
    )

    bot_message = await callback.message.answer(
        text,
        reply_markup=keyboards.back_to_adminpanel
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(AdminStates.action_end)


def count_all_users(database: Database) -> int:
    return database.session.query(User).count()


def count_clients(database: Database) -> int:
    users_with_payments = database.session.query(
        Payment.user_id
    ).distinct().subquery()

    return database.session.query(
        User
    ).filter(
        User.user_id.in_(users_with_payments)
    ).count()


def gender_percentage(database: Database) -> Tuple[float, float]:
    male_count = database.session.query(
        User
    ).filter_by(
        gender="male"
    ).count()

    female_count = database.session.query(
        User
    ).filter_by(
        gender="female"
    ).count()
    
    total_specified_gender = male_count + female_count  # только те, кто указал пол
    
    # Проверка на ноль, чтобы избежать деления на ноль
    if total_specified_gender == 0:
        return 0.0, 0.0

    male_percentage = round((male_count / total_specified_gender) * 100, 2)
    female_percentage = round((female_count / total_specified_gender) * 100, 2)

    return male_percentage, female_percentage


def count_subscriptions(database: Database) -> dict:
    now = datetime.utcnow()
    subscription_counts = {
        1: 0,
        2: 0,
        3: 0,
        6: 0,
        12: 0
    }

    for period in subscription_counts.keys():
        payments = database.get_payments(period=period)

        for payment in payments:
            end_date = datetime.strptime(
                payment.ended_at, 
                database_datetime_format
            )
            if now < end_date:
                subscription_counts[period] += 1

    return subscription_counts

def total_revenue(database: Database) -> float:
    payments = database.get_payments(status='success')
    total = 0.0

    for payment in payments:
        total += months_to_rub_price[payment.period]

    return total

def count_total_transactions(database: Database) -> int:
    return database.session.query(
        Payment
    ).filter(
        Payment.status != 'pending'
    ).count()
    
def count_successful_transactions(database: Database) -> int:
    return database.session.query(
        Payment
    ).filter_by(
        status='success'
    ).count()

