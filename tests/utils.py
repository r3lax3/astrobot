from datetime import datetime, timedelta


def current_month_period():
    today = datetime.today()
    start_of_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        end_of_month = datetime(
            today.year + 1,
            1,
            1
        ) - timedelta(days=1)
    else:
        end_of_month = datetime(
            today.year,
            today.month + 1,
            1
        ) - timedelta(days=1)
    return start_of_month, end_of_month
