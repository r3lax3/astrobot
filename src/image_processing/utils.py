from aiogram.types import BufferedInputFile

from typing import Optional, Dict
from datetime import datetime, timedelta, date

from src import config, messages
from src.enums import (
    ZodiacSign, 
    FileName,
    MoonSignInterpretationType
)
from src.database import Database
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.astro_engine.moon import (
    get_main_lunar_day_at_date, 
    get_next_lunar_day, 
    get_moon_phase,
    get_moon_signs_at_date 
)
from src.image_processing.generate_images import generate_image_with_astrodata
from src.translations import (
    ZODIAC_RU_TRANSLATION, 
    MOON_PHASE_RU_TRANSLATIONS
)


# Get the date format from the configuration
DATE_FORMAT: str = config.get('database.date_format')

DATETIME_FORMAT: str = config.get('database.datetime_format')
DATE_FORMAT: str = config.get('database.date_format')
TIME_FORMAT: str = config.get('database.time_format')

MOON_IN_SIGNS_INTERPRETATIONS = get_moon_in_signs_interpretations()


def get_interpretation(
    sign: str,
    interpretation_type: MoonSignInterpretationType
) -> str:
    if interpretation_type == MoonSignInterpretationType.GENERAL:
        return MOON_IN_SIGNS_INTERPRETATIONS[sign]['general']
    else:
        _messages = {
            MoonSignInterpretationType.FAVORABLE: messages.moon_sign_favourable,
            MoonSignInterpretationType.UNFAVORABLE: messages.moon_sign_unfavourable
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

    Эта функция вычисляет текущий и следующий лунные дни, а также описание фазы Луны,
    и форматирует эти данные в текст.

    Args:
        utc_date (datetime): Текущая дата и время в UTC.
        longitude (float): Долгота наблюдателя.
        latitude (float): Широта наблюдателя.
        timezone_offset (int): Смещение временной зоны от UTC.

    Returns:
        str: Описание фазы Луны и лунных дней.
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
        next_lunar_day_start_str = f'{next_lunar_day_start_time_str} след. дня'
    else:
        next_lunar_day_start_str = next_lunar_day_start_time_str

    text = messages.moon_phase_caption.format(
        current_lunar_day_number=current_lunar_day.number,
        moon_phase=moon_phase_str,
        next_lunar_day_start=next_lunar_day_start_str,
        next_lunar_day_number=next_lunar_day.number
    )

    return text


def get_image_with_astrodata(
    user, 
    database: Database,
    moon_signs: Optional[Dict] = None,
) -> bytes:
    date = (datetime.utcnow() + timedelta(hours=user.timezone_offset)).date()
    if moon_signs is None:
        # Getting image
        timezone_offset: int = user.timezone_offset

        moon_signs = get_moon_signs_at_date(
            date,  # %Y-%m-%d, not datetime
            timezone_offset,
            user.current_location
        )

    timezone_offset = user.timezone_offset

    current_user_location = database.get_location(user.current_location_id)
    longitude = current_user_location.longitude
    latitude = current_user_location.latitude

    moon_phase = get_moon_phase(
        date, 
        longitude,
        latitude
    )
    # print(f'Фаза на картинке: {moon_phase}')

    moon_phase_caption = get_moon_phase_caption(
        date,
        longitude, 
        latitude,
        user.timezone_offset
    )

    start_sign: Optional[ZodiacSign] = moon_signs.get('start_sign', None)
    change_time: Optional[str] = moon_signs.get('change_time', None)
    end_sign: Optional[ZodiacSign] = moon_signs.get('end_sign', None)

    photo = generate_image_with_astrodata(
        date=date.strftime(DATE_FORMAT),
        moon_phase=moon_phase,
        moon_phase_caption=moon_phase_caption,
        change_time=change_time,
        start_sign=start_sign,
        end_sign=end_sign
    )
    return photo

