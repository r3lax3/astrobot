"""Утилиты для интеграции с Prodamus.

Prodamus подписывает данные PHP-скриптом, поэтому подпись и query-строка
должны байт-в-байт повторять поведение PHP (json_encode с экранированием
слэшей, http_build_query с индексами вложенных массивов).
"""
import hmac
import json

from typing import Any
from urllib.parse import quote_plus


class Hmac:
    """HMAC-подпись данных в формате, совместимом с PHP-SDK Prodamus."""

    @staticmethod
    def create(data: dict, key: str, algo: str = 'sha256') -> str:
        data = Hmac._str_val_and_sort(data)

        # Повторяем PHP json_encode: без пробелов и с экранированием "/"
        data_str = json.dumps(
            data,
            separators=(',', ':'),
            ensure_ascii=False
        ).replace('/', '\\/')

        return hmac.new(
            key.encode('utf-8'),
            data_str.encode('utf-8'),
            algo
        ).hexdigest()

    @staticmethod
    def verify(data: dict, key: str, signature: str) -> bool:
        """Сверяет подпись входящего вебхука с вычисленной."""
        expected = Hmac.create(data, key)
        return hmac.compare_digest(expected, signature)

    @classmethod
    def _str_val_and_sort(cls, data: dict) -> dict:
        """Рекурсивно приводит значения к строкам и сортирует ключи."""
        data = {key: data[key] for key in sorted(data)}
        for item in data:
            if isinstance(data[item], dict):
                data[item] = cls._str_val_and_sort(data[item])
            elif isinstance(data[item], list):
                data[item] = [
                    cls._str_val_and_sort(elem)
                    if isinstance(elem, dict)
                    else str(elem) for elem in data[item]
                ]
            else:
                data[item] = str(data[item])

        return data


def http_build_query(data: dict) -> str:
    """Аналог PHP http_build_query: вложенные структуры кодируются
    как key[0][subkey]=value."""
    return '&'.join(
        f"{quote_plus(str(key))}={quote_plus(str(value))}"
        for key, value in _flatten(data)
    )


def parse_php_query(items: Any) -> dict:
    """Обратная операция к http_build_query: собирает пары вида
    ("products[0][name]", "...") обратно во вложенный словарь.

    Словари с последовательными числовыми ключами ("0", "1", ...)
    превращаются в списки — так же их сериализует PHP json_encode,
    иначе подпись не совпадёт.
    """
    result: dict = {}
    for raw_key, value in items:
        parts = raw_key.replace(']', '').split('[')
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value

    return _listify_numeric_keys(result)


def _listify_numeric_keys(data: dict) -> Any:
    nested = {
        key: _listify_numeric_keys(value) if isinstance(value, dict) else value
        for key, value in data.items()
    }

    if nested and all(key.isdigit() for key in nested):
        keys = sorted(nested, key=int)
        if [int(key) for key in keys] == list(range(len(keys))):
            return [nested[key] for key in keys]

    return nested


def _flatten(data: Any, prefix: str = '') -> list[tuple[str, Any]]:
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, (list, tuple)):
        items = enumerate(data)
    else:
        return [(prefix, data)]

    pairs = []
    for key, value in items:
        full_key = f"{prefix}[{key}]" if prefix else str(key)
        pairs.extend(_flatten(value, full_key))

    return pairs
