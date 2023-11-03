import ephem

from datetime import datetime, timedelta
from typing import List

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import User

from src import config
from src.routers import messages
from src.routers.states import MainMenu
from src.keyboard_manager import KeyboardManager, bt
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
        "Овен",
    "Taurus": 
        "Телец",
    "Gemini": 
        "Близнецы",
    "Cancer": 
        "Рак",
    "Leo":
        "Лев",
    "Virgo": 
        "Дева",
    "Libra": 
        "Весы",
    "Scorpio":  
        "Скорпион",
    "Sagittarius": 
        "Стрелец",
    "Capricorn": 
        "Козерог",
    "Aquarius": 
        "Водолей",
    "Pisces": 
        "Рыбы"
}


def translate_to_russian(english_name):
    return zodiac_translation.get(english_name, "Неизвестный знак")


def get_moon_sign(date_time: datetime):
    moon = ephem.Moon(date_time)
    return ephem.constellation(moon)[1]


def find_moon_sign_change(date: datetime, timezone_offset: int) -> dict:
    date = date.replace(hour=0, minute=0)

    start_of_day = datetime.strptime(date, date_format) + timedelta(hours=timezone_offset)
    end_of_day = start_of_day + timedelta(hours=23, minutes=59)
    
    start_sign = get_moon_sign(start_of_day)
    end_sign = get_moon_sign(end_of_day)
    
    result = {
        "start_sign": translate_to_russian(start_sign)
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
        result["end_sign"] = translate_to_russian(end_sign)
    
    return result


def get_formatted_moon_sign_text(
    date: datetime, 
    timezone_offset: int
) -> str:
    moon_signs = find_moon_sign_change(date, timezone_offset)
    if moon_signs.get('change_time', False):
        
    else:
        ...

