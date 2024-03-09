import os
import sys
import logging
import hashlib
import hmac
import json
import pytz
import yaml
import pandas as pd

from datetime import datetime, timedelta
from typing import Any, List
from dataclasses import is_dataclass, asdict

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from src import messages
from src.exceptions import PathDoesNotExistError


geolocator = Nominatim(user_agent="AstroBot")


class Hmac:
    @staticmethod
    def create(data, key: str, algo='sha256'):
        # Приведение всех значений к строкам и сортировка
        data = Hmac._str_val_and_sort(data)
        # Подготовка строки для хэширования
        data_str = json.dumps(
            data,
            separators=(',', ':'),
            ensure_ascii=False
        ).replace('/', '\\/')

        data_binary = data_str.encode('utf-8')

        with open('tests/hmac_data.txt', 'wb') as f:
            f.write(data_binary)

        # Вычисление HMAC
        return hmac.new(
            key.encode('utf-8'),
            data_binary,
            algo
        ).hexdigest()

    @classmethod
    def _str_val_and_sort(self, data):
        """Рекурсивно преобразует значения словаря в строки и сортирует ключи."""
        data = self._sort_object(data)
        for item in list(data.keys()):
            if isinstance(data[item], dict):  # Если значение является словарем
                data[item] = self._str_val_and_sort(data[item])
            elif isinstance(data[item], list):  # Если значение является списком
                # Преобразуем каждый элемент списка отдельно, если это необходимо
                data[item] = [
                    self._str_val_and_sort(elem)
                    if isinstance(elem, dict)
                    else str(elem) for elem in data[item]
                ]
            else:
                data[item] = str(data[item])

        return data

    @classmethod
    def _sort_object(self, obj):
        """Возвращает новый словарь с отсортированными ключами."""
        if not isinstance(obj, dict):
            return obj

        # Создаем новый словарь с тем же содержимым, но с отсортированными ключами
        sorted_obj = {key: obj[key] for key in sorted(obj)}  # python3.7 или выше
        return sorted_obj


def load_yaml(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_timezone_offset(latitude: float, longitude: float) -> int:
    obj = TimezoneFinder()
    tz_name = obj.timezone_at(
        lat=latitude, lng=longitude
    )  # Получаем имя временной зоны
    if tz_name:
        timezone = pytz.timezone(tz_name)
        offset = timezone.utcoffset(datetime.utcnow())
        return int(offset.total_seconds() / 3600)  # Преобразуем в часы
    else:
        raise Exception(f"Can't get timezone name. {latitude = }, {longitude = }")


def get_timezone_str_from_coords(longitude: float, latitude: float) -> str:
    """
    Get the timezone for given latitude and longitude coordinates.

    Args:
    latitude (float): Latitude of the location.
    longitude (float): Longitude of the location.

    Returns:
    str: Timezone for the given coordinates.
    """
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=latitude, lng=longitude)

    if timezone_str:
        return timezone_str
    else:
        raise ValueError(
            (
                "Timezone could not be determined for the coordinates: "
                f"Latitude {latitude}, Longitude {longitude}"
            )
        )


def get_timezone_str_from_offset(timezone_offset: int) -> str:
    for tz in pytz.all_timezones:
        timezone = pytz.timezone(tz)
        now = datetime.now(timezone)
        offset = now.utcoffset().total_seconds() / 3600
        if round(offset) == timezone_offset:
            return tz


def convert_to_utc(dt: datetime, offset: int) -> datetime:
    return dt - timedelta(hours=offset)


def convert_from_utc(dt: datetime, offset: int) -> datetime:
    return dt + timedelta(hours=offset)


def is_int(string: str) -> bool:
    try:
        int(string)
        return True
    except (TypeError, ValueError):
        return False


def split_list(input_list: list, sublist_len: int = 2):
    """
    [1, 2, 3, 4] -> [[1, 2], [3, 4]]

    Типа дробит список на подсписки с определённой длинной
    Если список не делится нацело - остаток запихнёт в последний подсписок

    [1, 2, 3, 4, 5] -> [[1, 2], [3, 4], [5]]
    """
    return [
        input_list[i : i + sublist_len] for i in range(0, len(input_list), sublist_len)
    ]


def get_location_by_coords(longitude: float, latitude: float) -> str:
    location = geolocator.reverse(
        (latitude, longitude), language="ru", exactly_one=True
    )

    if location and "address" in location.raw:
        address_info = location.raw["address"]

        # Вытягиваю наружу нужные мне данные из дикта
        city = address_info.get("city", "")
        town = address_info.get("town", "")
        village = address_info.get("village", "")
        region = address_info.get("region", "")
        district = address_info.get("district", "")
        state = address_info.get("state", "")
        country = address_info.get("country", "")

        if city:
            return f"{city}, {state}, {country}"
        elif region:
            return f"{region}, {state}, {country}"
        elif town:
            return f"{town}, {district}, {state}, {country}"
        elif village:
            return f"{village}, {district}, {state}, {country}"
        else:
            return country

    return messages.ERROR_MESSAGE


def path_validation(path: str) -> None:
    if not os.path.exists(path):
        raise PathDoesNotExistError(f"Путь не существует: {path}")


def in_range(value: Any, start: Any, end: Any) -> bool:
    return start <= value < end


def logger_settings():
    """
    Настройки логгирования, вызывается только в ~/main.py
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, encoding="utf-8")
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)


def generate_random_sha1_key() -> str:
    # Generate random bytes
    random_bytes = os.urandom(20)

    # Create a SHA1 hash object
    sha1_hash = hashlib.sha1()

    # Update the hash object with the random bytes
    sha1_hash.update(random_bytes)

    # Generate the SHA1 hash (in hexadecimal format)
    sha1_key = sha1_hash.hexdigest()

    return sha1_key


async def delete_message(message: Message):
    """
    Удаляет сообщение без возвращения ошибки
    """
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


def format_time_delta(delta_time: timedelta) -> str:
    """
    Форматирует объект timedelta в строку, отображающую оставшееся время.

    Если какая-либо часть времени (дни, часы, минуты) равна нулю, она не включается в итоговую строку.
    Например, "1 д. 3 ч." или "2 ч. 15 мин.", или "Меньше минуты" для очень малых значений.

    Args:
    -----
    delta_time (timedelta): Разница во времени, которую необходимо форматировать.

    Returns:
    --------
    str: Строка, представляющая оставшееся время в формате "х д. х ч. х мин." или "Меньше минуты".
    """

    # Извлекаем дни, часы и минуты из delta_time
    days = delta_time.days
    hours, remainder = divmod(delta_time.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    # Собираем строку, исключая нулевые значения
    time_parts = []
    if days > 0:
        time_parts.append(f"{days} д.")
    if hours > 0:
        time_parts.append(f"{hours} ч.")
    if minutes > 0:
        time_parts.append(f"{minutes} мин.")

    # Возвращаем сформированную строку или "Меньше минуты" при отсутствии значительного оставшегося времени
    return ' '.join(time_parts) if time_parts else "Меньше минуты"


def print_items_dict_as_table(items: list[Any], file=None) -> None:
    if len(items) == 0:
        print('No data to print!')

    if is_dataclass(items[0]):
        items = [asdict(item) for item in items]

    if not isinstance(items[0], dict):
        print("Can't print not dict-like objects")
        return

    # Создание DataFrame из списка словарей
    df = pd.DataFrame(items)

    # Вывод DataFrame в формате Markdown с помощью fancy_grid
    print(df.to_markdown(index=False), file=file)


def get_average_datetime(datetimes: List[datetime]) -> datetime:
    """Возвращает средний арифметический datetime из списка."""
    if len(datetimes) == 0:
        return

    timestamps = [dt.timestamp() for dt in datetimes]
    average_timestamp = sum(timestamps) / len(timestamps)

    return datetime.fromtimestamp(average_timestamp)
