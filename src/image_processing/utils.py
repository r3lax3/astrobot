import logging

from datetime import date, datetime, timedelta
from typing import Dict, Optional

from src import config, messages
from src.astro_engine.moon import (
    get_main_lunar_day_at_date,
    get_moon_phase,
    get_moon_signs_at_date,
    get_next_lunar_day,
    get_blank_moon_period
)
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.astro_engine.models import User as AstroUser
from src.enums import MoonSignInterpretationType, ZodiacSign
from src.image_processing.generate_images import generate_image_with_astrodata
from src.translations import MOON_PHASE_RU_TRANSLATIONS


# Get the date format from the configuration
DATE_FORMAT: str = config.get("database.date_format")

DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
TIME_FORMAT: str = config.get("database.time_format")

MOON_IN_SIGNS_INTERPRETATIONS = get_moon_in_signs_interpretations()

LOGGER = logging.getlogger(__name__)


def get_interpretation(
    sign: str,
    interpretation_type: MoonSignInterpretationType
) -> str:
    if interpretation_type == MoonSignInterpretationType.GENERAL:
        return MOON_IN_SIGNS_INTERPRETATIONS[sign]["general"]
    else:
        _messages = {
            MoonSignInterpretationType.FAVORABLE: messages.MOON_SIGN_FAVOURABLE,
            MoonSignInterpretationType.UNFAVORABLE: messages.MOON_SIGN_UNFAVOURABLE,
        }
        message = _messages[interpretation_type]
        return message.format(
            text=MOON_IN_SIGNS_INTERPRETATIONS[sign][interpretation_type.value]
        )


def get_moon_phase_caption(
    utcdate: date,
    longitude: float,
    latitude: float,
    timezone_offset: int
) -> str:
    """
    Генерирует описание фазы Луны для заданного времени и местоположения.

    Эта функция вычисляет текущий и следующий лунные дни, а также 
    описание фазы Луны и форматирует эти данные в текст.
    """
    utcdate = datetime(utcdate.year, utcdate.month, utcdate.day)

    current_lunar_day = get_main_lunar_day_at_date(utcdate, longitude, latitude)
    next_lunar_day = get_next_lunar_day(current_lunar_day, longitude, latitude)

    moon_phase = get_moon_phase(utcdate, longitude, latitude)
    # print(f'Фаза в описании: {moon_phase}')
    moon_phase_str = MOON_PHASE_RU_TRANSLATIONS.get(moon_phase, "Неизвестная фаза")

    next_lunar_day_start_time_str = (
        next_lunar_day.start + timedelta(hours=timezone_offset)
    ).strftime(TIME_FORMAT)

    if utcdate + timedelta(hours=24) < next_lunar_day.start:
        next_lunar_day_start_str = f"{next_lunar_day_start_time_str} след. дня"
    else:
        next_lunar_day_start_str = next_lunar_day_start_time_str

    text = messages.MOON_PHASE_CAPTION.format(
        current_lunar_day_number=current_lunar_day.number,
        moon_phase=moon_phase_str,
        next_lunar_day_start=next_lunar_day_start_str,
        next_lunar_day_number=next_lunar_day.number,
    )

    return text


async def get_image_with_astrodata(
    user,
    moon_signs: Optional[Dict] = None,
    date: Optional[datetime] = None
) -> bytes:
    utcdate = datetime.utcnow()

    if date is None:
        date = (utcdate + timedelta(hours=user.timezone_offset)).date()

    if moon_signs is None:
        # Getting image
        timezone_offset: int = user.timezone_offset

        moon_signs = get_moon_signs_at_date(
            date,  # date is %Y-%m-%d, not datetime
            timezone_offset,
            user.current_location
        )

    timezone_offset = user.timezone_offset

    current_user_location = user.current_location
    longitude = current_user_location.longitude
    latitude = current_user_location.latitude

    moon_phase = get_moon_phase(date, longitude, latitude)

    moon_phase_caption = get_moon_phase_caption(
        date,
        longitude,
        latitude,
        user.timezone_offset
    )

    start_sign: Optional[ZodiacSign] = moon_signs.get("start_sign", None)
    change_time: Optional[str] = moon_signs.get("change_time", None)
    end_sign: Optional[ZodiacSign] = moon_signs.get("end_sign", None)

    blank_moon_caption = get_blank_moon_caption(date, user, timezone_offset)

    photo = generate_image_with_astrodata(
        date=date.strftime(DATE_FORMAT),
        moon_phase=moon_phase,
        moon_phase_caption=moon_phase_caption,
        change_time=change_time,
        start_sign=start_sign,
        end_sign=end_sign,
        blank_moon_caption=blank_moon_caption
    )
    return photo


def get_blank_moon_caption(
    date: date,
    user,
    timezone_offset: int
) -> str:
    astrouser = AstroUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=user.birth_location,
        current_location=user.current_location
    )

    datetime_obj = datetime(date.year, date.month, date.day)

    blank_moon_period = get_blank_moon_period(
        datetime_obj,
        astrouser,
        timezone_offset
    )

    LOGGER.info(
        '\nBlank moon period:\n\nstart: {start}\nend: {end}'.format(
            start=blank_moon_period.start.strftime(DATETIME_FORMAT),
            end=blank_moon_period.end.strftime(DATETIME_FORMAT)
        )
    )

    today = datetime_obj.date()
    yesterday = today - timedelta(days=1)

    start_date = blank_moon_period.start.date()

    start_today = start_date == today
    start_yesterday = start_date == yesterday

    end_today = today == blank_moon_period.end.date()

    if not (start_today or start_yesterday):
        return 'Холостая луна сегодня отсутствует'

    start_time_str = blank_moon_period.start.strftime(TIME_FORMAT)
    if start_yesterday:
        start_time_str = '00:00'

    end_time_str = '23:59'
    if end_today:
        end_time_str = blank_moon_period.end.strftime(TIME_FORMAT)

    return f'Холостая луна {start_time_str} - {end_time_str}'
