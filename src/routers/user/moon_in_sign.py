import csv

import ephem

from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User

from src import config
from src.routers import messages
from src.routers.states import MainMenu
from src.keyboard_manager import (
    KeyboardManager, 
    bt, 
    from_text_to_bt
)
from src.database import Database


r = Router()

date_format: str = config.get(
    'database.date_format'
)
time_format: str = config.get(
    'database.time_format'
)
zodiac_translation = {
    "Aries": 
        "Овне",
    "Taurus": 
        "Тельце",
    "Gemini": 
        "Близнецах",
    "Cancer": 
        "Раке",
    "Leo":
        "Льве",
    "Virgo": 
        "Деве",
    "Libra": 
        "Весах",
    "Scorpio":  
        "Скорпионе",
    "Sagittarius": 
        "Стрельце",
    "Capricorn": 
        "Козероге",
    "Aquarius": 
        "Водолее",
    "Pisces": 
        "Рыбах"
}

# Путь к вашему CSV файлу
moon_in_sign_csv_file_path = './moon_in_sign.csv'

# Словарь, который будет содержать данные
moon_in_signs_interpretation = {}

# Чтение CSV файла и заполнение словаря
with open(
    moon_in_sign_csv_file_path, 
    mode='r', 
    encoding='utf-8'
) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        sign = row['sign']
        moon_in_signs_interpretation[sign] = {
            'general': row['general'],
            'favorable': row['favorable'],
            'unfavorable': row['unfavorable']
        }


def translate_to_russian(english_name: str):
    return zodiac_translation.get(
        english_name, 
        "Неизвестный знак"
    )


def get_moon_sign(date_time: datetime):
    moon = ephem.Moon(date_time)
    return ephem.constellation(moon)[1]


def find_moon_sign_change(
    date: datetime, 
    timezone_offset: int
) -> dict:
    date = date.replace(hour=0, minute=0)

    start_of_day = date + timedelta(hours=timezone_offset)
    end_of_day = start_of_day + timedelta(hours=23, minutes=58)
    
    start_sign = get_moon_sign(start_of_day)
    end_sign = get_moon_sign(end_of_day)
    
    result = {
        "start_sign": start_sign
    }
    
    if start_sign != end_sign:
        # Бинарный поиск времени смены знака
        left_time = start_of_day
        right_time = end_of_day

        while (right_time - left_time).total_seconds() > 60:  # пока разница во времени больше минуты
            middle_time = left_time + (right_time - left_time) / 2
            if get_moon_sign(middle_time) == start_sign:
                left_time = middle_time
            else:
                right_time = middle_time
        change_time = left_time

        result["change_time"] = change_time.strftime("%H:%M")
        result["end_sign"] = end_sign
    
    return result


def get_formatted_moon_sign_text(
    moon_signs: dict,
    type: str
) -> str:
    if type not in ['general', 'favorable', 'unfavorable']:
        raise Exception('Unexpected type of text for moon sign!')
    sign_changed_time: str = moon_signs.get('change_time', False)  # time in format %H:%m

    if sign_changed_time:
        match type:
            case 'general':
                first_sign = moon_signs['start_sign']
                second_sign = moon_signs['end_sign']

                first_part = moon_in_signs_interpretation[first_sign]['general']
                second_part = moon_in_signs_interpretation[second_sign]['general']
            case 'favorable':
                first_sign = moon_signs['start_sign']
                second_sign = moon_signs['end_sign']

                first_part = messages.moon_sign_favourable.format(
                    text = moon_in_signs_interpretation[first_sign]['favorable']
                )
                second_part = messages.moon_sign_favourable.format(
                    text = moon_in_signs_interpretation[second_sign]['favorable']
                )
            case 'unfavorable':
                first_sign = moon_signs['start_sign']
                second_sign = moon_signs['end_sign']

                first_part = messages.moon_sign_unfavourable.format(
                    text = moon_in_signs_interpretation[first_sign]['unfavorable']
                )
                second_part = messages.moon_sign_unfavourable.format(
                    text = moon_in_signs_interpretation[second_sign]['unfavorable']
                )
        
        # Преобразование строки в объект datetime
        time_obj = datetime.strptime(
            sign_changed_time,
            "%H:%M"
        )

        # Добавление одной минуты
        time_with_added_minute = time_obj + timedelta(minutes=1)
        time_str_with_added_minute = time_with_added_minute.strftime("%H:%M")

        text = messages.moon_sign_changed.format(
            first_time=sign_changed_time,
            second_time=time_str_with_added_minute,
            start_sign=translate_to_russian(first_sign),  # Из "Aries" в "Овна"
            end_sign=translate_to_russian(second_sign),  # Тут тоже
            first_part=first_part,
            second_part=second_part
        )

    else:
        match type:
            case 'general':
                sign = moon_signs['start_sign']

                interpretation_str = moon_in_signs_interpretation[sign]['general']
            case 'favorable':
                sign = moon_signs['start_sign']

                interpretation_str = messages.moon_sign_favourable.format(
                    text = moon_in_signs_interpretation[sign]['favorable']
                )

            case 'unfavorable':
                sign = moon_signs['start_sign']

                interpretation_str = messages.moon_sign_unfavourable.format(
                    text = moon_in_signs_interpretation[sign]['unfavorable']
                )

        text = messages.moon_sign_not_changed.format(
            start_sign=translate_to_russian(sign),
            text=interpretation_str
        )

    return text


@r.message(F.text, F.text == bt.moon_in_sign)
async def general_moon_sign_menu(
    message: Message,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    user = database.get_user(event_from_user.id)
    
    timezone_offset: int = user.timezone_offset

    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)
    moon_signs = find_moon_sign_change(
        date,
        timezone_offset
    )
    text = get_formatted_moon_sign_text(
        moon_signs, 
        type='general'
    )

    bot_message = await message.answer(
        text,
        reply_markup=keyboards.moon_in_sign_menu
    )
    await state.update_data(
        del_messages=[bot_message.message_id],
        timezone_offset=timezone_offset
    )
    await state.set_state(MainMenu.moon_in_sign_general)


@r.callback_query(F.data == bt.moon_in_sign)
@r.callback_query(
    MainMenu.moon_in_sign_description, 
    F.data == bt.back
)
async def general_moon_sign_menu_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
    database: Database,
    event_from_user: User
):
    await general_moon_sign_menu(
        callback.message,
        state,
        keyboards,
        database,
        event_from_user
    )


@r.callback_query(
    MainMenu.moon_in_sign_general,
    F.data.in_(
        [
            bt.favorable, 
            bt.unfavorable
        ]
    )
)
async def moon_in_sign_description(
    callback: CallbackQuery,
    state: FSMContext,
    keyboards: KeyboardManager,
):
    data = await state.get_data()
    timezone_offset: int = data['timezone_offset']

    date: datetime = datetime.utcnow() + timedelta(hours=timezone_offset)
    moon_signs = find_moon_sign_change(date, timezone_offset)
    text = get_formatted_moon_sign_text(
        moon_signs,
        type=from_text_to_bt[callback.data]
    )
    bot_message = await callback.message.answer(
        text,
        reply_markup=keyboards.back
    )
    await state.update_data(
        del_messages=[bot_message.message_id]
    )
    await state.set_state(
        MainMenu.moon_in_sign_description
    )

