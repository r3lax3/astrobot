from datetime import datetime, timedelta

from aiogram.types import BufferedInputFile

from src import config, messages
from src.enums import MoonSignInterpretationType, MoonPhase, ZodiacSign, FileName
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.astro_engine.moon import (
    get_main_lunar_day_at_date, 
    get_next_lunar_day, 
    get_moon_phase
)
from src.image_processing import generate_image_for_moon_signs


DATETIME_FORMAT: str = config.get('database.datetime_format')
DATE_FORMAT: str = config.get('database.date_format')
TIME_FORMAT: str = config.get('database.time_format')

MOON_IN_SIGNS_INTERPRETATIONS = get_moon_in_signs_interpretations()

ZODIAC_RU_TRANSLATION = {
    ZodiacSign.ARIES: "Овне",
    ZodiacSign.TAURUS: "Тельце",
    ZodiacSign.GEMINI: "Близнецах",
    ZodiacSign.CANCER: "Раке",
    ZodiacSign.LEO: "Льве",
    ZodiacSign.VIRGO: "Деве",
    ZodiacSign.LIBRA: "Весах",
    ZodiacSign.SCORPIO: "Скорпионе",
    ZodiacSign.SAGITTARIUS: "Стрельце",
    ZodiacSign.CAPRICORN: "Козероге",
    ZodiacSign.AQUARIUS: "Водолее",
    ZodiacSign.PISCES: "Рыбах"
}
MOON_PHASE_RU_TRANSLATIONS = {
    MoonPhase.NEW_MOON: "НОВОЛУНИЕ",
    MoonPhase.WAXING_CRESCENT: "РАСТУЩИЙ ПОЛУМЕСЯЦ",
    MoonPhase.FIRST_QUARTER: "ПЕРВАЯ ЧЕТВЕРТЬ",
    MoonPhase.WAXING_GIBBOUS: "РАСТУЩАЯ ЛУНА",
    MoonPhase.FULL_MOON: "ПОЛНОЛУНИЕ",
    MoonPhase.WANING_GIBBOUS: "УБЫВАЮЩАЯ ЛУНА",
    MoonPhase.LAST_QUARTER: "ПОСЛЕДНЯЯ ЧЕТВЕРТЬ",
    MoonPhase.WANING_CRESCENT: "УБЫВАЮЩИЙ ПОЛУМЕСЯЦ"
}


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
        return message.format(text=MOON_IN_SIGNS_INTERPRETATIONS[sign][interpretation_type.value])


def get_formatted_moon_sign_text(
    moon_signs: dict, 
    interpretation_type: MoonSignInterpretationType
) -> str:
    sign_changed_time: str = moon_signs.get('change_time', False)

    if sign_changed_time:
        first_sign = moon_signs['start_sign']
        second_sign = moon_signs['end_sign']

        first_part = get_interpretation(first_sign.value, interpretation_type)
        second_part = get_interpretation(second_sign.value, interpretation_type)

        time_obj = datetime.strptime(sign_changed_time, TIME_FORMAT)
        time_with_added_minute = time_obj + timedelta(minutes=1)
        time_str_with_added_minute = time_with_added_minute.strftime(TIME_FORMAT)

        text = messages.moon_sign_changed.format(
            first_time=sign_changed_time,
            second_time=time_str_with_added_minute,
            start_sign=ZODIAC_RU_TRANSLATION.get(first_sign, "Неизвестный знак"),
            end_sign=ZODIAC_RU_TRANSLATION.get(second_sign, "Неизвестный знак"),
            first_part=first_part,
            second_part=second_part
        )
    else:
        sign = moon_signs['start_sign']
        interpretation_str = get_interpretation(sign.value, interpretation_type)
        text = messages.moon_sign_not_changed.format(
            start_sign=ZODIAC_RU_TRANSLATION.get(sign, "Неизвестный знак"),
            text=interpretation_str
        )

    return text


def get_moon_phase_caption(
    utc_date: datetime,
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
    utc_date = datetime.utcnow().replace(hour=0, minute=0) - timedelta(hours=timezone_offset)

    current_lunar_day = get_main_lunar_day_at_date(utc_date, longitude, latitude)
    next_lunar_day = get_next_lunar_day(current_lunar_day, longitude, latitude)

    moon_phase = get_moon_phase(utc_date, longitude, latitude)
    moon_phase_str = MOON_PHASE_RU_TRANSLATIONS.get(moon_phase, "Неизвестная фаза")

    next_lunar_day_start_time_str = (
        next_lunar_day.start + timedelta(hours=timezone_offset)
    ).strftime(TIME_FORMAT)

    if utc_date + timedelta(hours=24) < next_lunar_day.start:
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


def get_moon_signs_image(user, database, moon_signs):
    timezone_offset = user.timezone_offset
    date = datetime.utcnow() + timedelta(hours=timezone_offset)

    current_user_location = database.get_location(user.current_location_id)
    longitude = current_user_location.longitude
    latitude = current_user_location.latitude

    moon_phase = get_moon_phase(
        date, 
        longitude,
        latitude
    )

    moon_phase_caption = get_moon_phase_caption(
        date,
        longitude, 
        latitude,
        user.timezone_offset
    )

    start_sign: ZodiacSign = moon_signs.get('start_sign', None)
    end_sign: ZodiacSign = moon_signs.get('end_sign', None)

    photo = BufferedInputFile(
        file=generate_image_for_moon_signs(
            date=date.strftime(DATE_FORMAT),
            moon_phase=moon_phase,
            moon_phase_caption=moon_phase_caption,
            start_sign=start_sign,
            end_sign=end_sign
        ),
        filename=FileName.MOON_SIGN.value
    )
    return photo

