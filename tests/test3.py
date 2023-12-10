import ephem

from datetime import datetime, timedelta


LUNAR_MONTH = 29.53  # average length of a lunar month in days
LUNAR_DAY_LENGTH = LUNAR_MONTH / 30  # length of a lunar day in solar days
SECONDS_IN_DAY = 24 * 60 * 60


def get_lunar_day(date: datetime) -> int:
    """
    Calculate the lunar day for a given date.

    Args:
    date (datetime): The date for which to calculate the lunar day.

    Returns:
    int: The lunar day.
    """
    previous_new_moon = ephem.previous_new_moon(date).datetime()
    next_new_moon = ephem.next_new_moon(date).datetime()

    # Duration of the current lunar month
    lunar_month_duration: timedelta = next_new_moon - previous_new_moon
    lunar_month_duration_days = lunar_month_duration.total_seconds() / SECONDS_IN_DAY

    # Current age of the Moon in this lunar month
    lunar_age = date - previous_new_moon
    lunar_age_days = lunar_age.total_seconds() / SECONDS_IN_DAY

    # Calculate the lunar day as a proportion of the lunar month
    lunar_day = lunar_age_days / (lunar_month_duration_days / 30)
    lunar_day = lunar_day % 30

    return int(lunar_day) + 1


date = datetime.utcnow() - timedelta(days=28)
latitude = 55.7558
longitude = 37.6173
lunar_day = 0

for i in range(60*24*5):
    target_date = date + timedelta(minutes=i)

    target_lunar_day = get_lunar_day(target_date)

    if lunar_day != target_lunar_day:
        lunar_day = target_lunar_day
        
        my_date = target_date + timedelta(hours=3)

        print(f'{my_date.strftime("%d.%m.%Y %H:%M")}, {lunar_day} Лунный день')

