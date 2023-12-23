from datetime import datetime

from src import config, messages
from src.enums import MoonSignInterpretationType
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.translations import ZODIAC_RU_TRANSLATION


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

        time = datetime.strptime(sign_changed_time, TIME_FORMAT)
        time_str = time.strftime(TIME_FORMAT)

        text = messages.moon_sign_changed.format(
            first_time=sign_changed_time,
            second_time=time_str,
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

