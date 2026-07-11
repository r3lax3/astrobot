"""Утилиты для интеграции с Prodamus.

Prodamus подписывает данные PHP-скриптом (класс Hmac из их документации:
ksort -> strval всех значений -> json_encode(JSON_UNESCAPED_UNICODE) ->
hash_hmac sha256), поэтому подпись должна байт-в-байт повторять поведение
PHP. Эталон корректности — tests/test_payments.py::test_php_parity_fuzz,
который сверяет эту реализацию с оригинальным PHP-классом.
"""
import hmac
import json
import re

from functools import cmp_to_key
from typing import Any
from urllib.parse import quote_plus


# PHP is_numeric: целые/дробные/экспоненциальные строки, пробелы по краям
_PHP_NUMERIC = re.compile(r'\s*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?\s*')


def _php_key_cmp(a: str, b: str) -> int:
    """Порядок ключей PHP ksort(SORT_REGULAR): числовые строки
    сравниваются как числа ("9" < "10"), остальные пары — как строки.

    Если в одном словаре смешаны числовые и нечисловые ключи, у PHP
    сравнение нетранзитивно и итоговый порядок зависит от внутренностей
    zend_sort — такой случай не эмулируется (Prodamus ключи не смешивает:
    имена полей буквенные, индексы products числовые).
    """
    if _PHP_NUMERIC.fullmatch(a) and _PHP_NUMERIC.fullmatch(b):
        num_a, num_b = float(a), float(b)
        return (num_a > num_b) - (num_a < num_b)
    return (a > b) - (a < b)


class Hmac:
    """HMAC-подпись данных в формате, совместимом с PHP-SDK Prodamus."""

    @staticmethod
    def create(data: dict, key: str, algo: str = 'sha256') -> str:
        return hmac.new(
            key.encode('utf-8'),
            Hmac.canonical_json(data).encode('utf-8'),
            algo
        ).hexdigest()

    @staticmethod
    def verify(data: dict, key: str, signature: str) -> bool:
        """Сверяет подпись входящего вебхука с вычисленной.

        Как и PHP-эталон, не различает регистр hex-подписи.
        """
        if not signature:
            return False
        expected = Hmac.create(data, key)
        return hmac.compare_digest(expected, signature.lower())

    @staticmethod
    def canonical_json(data: dict) -> str:
        """Строка, которую подписывает Prodamus: PHP json_encode с флагом
        JSON_UNESCAPED_UNICODE. В отличие от json.dumps PHP экранирует
        "/" и разделители строк U+2028/U+2029."""
        data = Hmac._str_val_and_sort(data)
        return (
            json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            .replace('/', '\\/')
            .replace('\u2028', '\\u2028')
            .replace('\u2029', '\\u2029')
        )

    @classmethod
    def _str_val_and_sort(cls, data: dict) -> dict:
        """Рекурсивно приводит значения к строкам и сортирует ключи."""
        data = {
            key: data[key]
            for key in sorted(data, key=cmp_to_key(_php_key_cmp))
        }
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
    """Собирает пары вида ("products[0][name]", "...") во вложенный
    словарь так же, как PHP parse_str / $_POST:

    - "key[]" получает автоиндекс max(числовые ключи) + 1;
    - при конфликте скаляра и массива побеждает более поздний;
    - словари с ключами "0".."n-1" превращаются в списки — так их
      сериализует PHP json_encode, иначе подпись не совпадёт.
    """
    result: dict = {}
    for raw_key, value in items:
        parts = raw_key.replace(']', '').split('[')
        target = result
        for i, part in enumerate(parts):
            if part == '' and i > 0:
                part = str(_next_php_index(target))
            if i == len(parts) - 1:
                target[part] = value
            else:
                if not isinstance(target.get(part), dict):
                    target[part] = {}
                target = target[part]

    return _listify_numeric_keys(result)


def _next_php_index(container: dict) -> int:
    """Следующий автоиндекс PHP-массива: max целочисленных ключей + 1."""
    indices = [
        int(key) for key in container
        if key.lstrip('-').isdigit() and str(int(key)) == key
    ]
    return max(indices, default=-1) + 1


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
