from datetime import datetime, timedelta

from src import config, messages
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.enums import MoonSignInterpretationType


date_format: str = config.get('database.date_format')
time_format: str = config.get('database.time_format')

moon_in_signs_interpretations = get_moon_in_signs_interpretations()

zodiac_translation = {
    "Aries": "Овне",
    "Taurus": "Тельце",
    "Gemini": "Близнецах",
    "Cancer": "Раке",
    "Leo": "Льве",
    "Virgo": "Деве",
    "Libra": "Весах",
    "Scorpio": "Скорпионе",
    "Sagittarius": "Стрельце",
    "Capricorn": "Козероге",
    "Aquarius": "Водолее",
    "Pisces": "Рыбах"
}


def zodiac_sign_translate_to_russian(english_name: str):
    return zodiac_translation.get(
        english_name, 
        "Неизвестный знак"
    )


def get_interpretation(
    sign: str,
    interpretation_type: MoonSignInterpretationType
) -> str:
    if interpretation_type == MoonSignInterpretationType.GENERAL:
        return moon_in_signs_interpretations[sign]['general']
    else:
        _messages = {
            MoonSignInterpretationType.FAVORABLE: messages.moon_sign_favourable,
            MoonSignInterpretationType.UNFAVORABLE: messages.moon_sign_unfavourable
        }
        message = _messages[interpretation_type]
        return message.format(text=moon_in_signs_interpretations[sign][interpretation_type.value])


def get_formatted_moon_sign_text(
    moon_signs: dict, 
    interpretation_type: MoonSignInterpretationType
) -> str:
    sign_changed_time: str = moon_signs.get('change_time', False)

    if sign_changed_time:
        first_sign = moon_signs['start_sign']
        second_sign = moon_signs['end_sign']

        first_part = get_interpretation(first_sign, interpretation_type)
        second_part = get_interpretation(second_sign, interpretation_type)

        time_obj = datetime.strptime(sign_changed_time, time_format)
        time_with_added_minute = time_obj + timedelta(minutes=1)
        time_str_with_added_minute = time_with_added_minute.strftime(time_format)

        text = messages.moon_sign_changed.format(
            first_time=sign_changed_time,
            second_time=time_str_with_added_minute,
            start_sign=zodiac_sign_translate_to_russian(first_sign),
            end_sign=zodiac_sign_translate_to_russian(second_sign),
            first_part=first_part,
            second_part=second_part
        )
    else:
        sign = moon_signs['start_sign']
        interpretation_str = get_interpretation(sign, interpretation_type)
        text = messages.moon_sign_not_changed.format(
            start_sign=zodiac_sign_translate_to_russian(sign),
            text=interpretation_str
        )

    return text

