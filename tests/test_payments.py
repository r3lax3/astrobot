import os
import random
import shutil
import subprocess

import pytest

from urllib.parse import parse_qsl, quote_plus

from src.payments import ProdamusPaymentService
from src.payments.utils import Hmac, http_build_query, parse_php_query


TEST_KEY = 'test-secret-key'

# Данные и подпись в формате, который отдаёт PHP-SDK Prodamus
TEST_PAYLOAD = {
    'do': 'link',
    'products': [
        {
            'name': 'Подписка на Астропульс, 6 месяцев',
            'price': 2850,
            'quantity': 1,
            'paymentMethod': 4,
            'paymentObject': 4
        }
    ],
    'link_expired': '2024-02-15 23:32',
    'order_id': 'subscr:6:1060062986',
    'sys': '',
    'paid_content': 'https://t.me/AstroPulse_bot'
}
TEST_PAYLOAD_SIGN = (
    '444cdb62dad2a9b336cd43a8e548e1681bbf276f4587a6d74a8df7592b7881b3'
)

# Фикстуры вебхуков: тело запроса + подпись, вычисленная оригинальным
# PHP-классом Hmac из документации Prodamus (см. PHP_REFERENCE ниже):
#   parse_str($body, $post); Hmac::create($post, TEST_KEY);
WEBHOOK_BODY = (
    'date=2026-07-01T12%3A20%3A23%2B03%3A00&order_id=1'
    '&order_num=subscr%3A6%3A1060062986&domain=astropulse.payform.ru'
    '&sum=2850.00&currency=rub&customer_phone=%2B79998887766'
    '&customer_email=user%40example.com&customer_extra='
    '&payment_type=%D0%9E%D0%BF%D0%BB%D0%B0%D1%82%D0%B0+%D0%BA%D0%B0%D1%80'
    '%D1%82%D0%BE%D0%B9%2C+%D0%B2%D1%8B%D0%BF%D1%83%D1%89%D0%B5%D0%BD%D0%BD'
    '%D0%BE%D0%B9+%D0%B2+%D0%A0%D0%A4&commission=2.9&commission_sum=82.65'
    '&attempt=1&sys='
    '&products%5B0%5D%5Bname%5D=%D0%9F%D0%BE%D0%B4%D0%BF%D0%B8%D1%81%D0%BA'
    '%D0%B0+%D0%BD%D0%B0+%D0%90%D1%81%D1%82%D1%80%D0%BE%D0%BF%D1%83%D0%BB'
    '%D1%8C%D1%81%2C+6+%D0%BC%D0%B5%D1%81%D1%8F%D1%86%D0%B5%D0%B2'
    '&products%5B0%5D%5Bprice%5D=2850.00&products%5B0%5D%5Bquantity%5D=1'
    '&products%5B0%5D%5Bsum%5D=2850.00&payment_status=success'
    '&payment_status_description=%D0%A3%D1%81%D0%BF%D0%B5%D1%88%D0%BD'
    '%D0%B0%D1%8F+%D0%BE%D0%BF%D0%BB%D0%B0%D1%82%D0%B0'
)
WEBHOOK_SIGN = (
    '977907ed0defeb1cdc0dde7541ad28d569c61d6cfa6756758c1bafb9e8fb97d9'
)

# Крайние случаи PHP json_encode: слэши в url, разделитель строк U+2028,
# разреженные индексы products (2/9/10 -> json-объект с числовым порядком
# ключей), кавычки и бэкслэш в значении
TRICKY_WEBHOOK_BODY = (
    'paid_content=https%3A%2F%2Ft.me%2FAstroPulse_bot'
    '&order_num=subscr%3A1%3A42&note=line%E2%80%A8sep%E2%80%A9end'
    '&products%5B9%5D%5Bname%5D=%D0%A2%D0%B0%D1%80%D0%B8%D1%84+%22%D0%B4'
    '%D0%B5%D0%B2%D1%8F%D1%82%D1%8B%D0%B9%22+%5C+%D1%81%D0%BE+%D1%81%D0%BB'
    '%D1%8D%D1%88%D0%B5%D0%BC%2F'
    '&products%5B10%5D%5Bname%5D=%D0%B4%D0%B5%D1%81%D1%8F%D1%82%D1%8B%D0%B9'
    '&products%5B2%5D%5Bname%5D=%D0%B2%D1%82%D0%BE%D1%80%D0%BE%D0%B9'
    '&payment_status=success'
)
TRICKY_WEBHOOK_SIGN = (
    'b99f6bacf4f2cddecd826887002a9084dade68b940a73ffe1718ed87ec89717e'
)


def parse_webhook_body(body: str) -> dict:
    """Разбирает тело вебхука так же, как handle_payment_update."""
    return parse_php_query(parse_qsl(body, keep_blank_values=True))


def test_hmac_generation():
    assert Hmac.create(TEST_PAYLOAD, TEST_KEY, 'sha256') == TEST_PAYLOAD_SIGN


def test_hmac_verify():
    assert Hmac.verify(TEST_PAYLOAD, TEST_KEY, TEST_PAYLOAD_SIGN)
    assert not Hmac.verify(TEST_PAYLOAD, TEST_KEY, 'ff' * 32)
    assert not Hmac.verify(TEST_PAYLOAD, 'wrong-key', TEST_PAYLOAD_SIGN)


def test_hmac_verify_is_case_insensitive():
    """PHP-эталон сравнивает подписи через strtolower."""
    assert Hmac.verify(TEST_PAYLOAD, TEST_KEY, TEST_PAYLOAD_SIGN.upper())


def test_hmac_verify_rejects_empty_signature():
    assert not Hmac.verify(TEST_PAYLOAD, TEST_KEY, '')


def test_webhook_signature_matches_php_reference():
    payload = parse_webhook_body(WEBHOOK_BODY)
    assert Hmac.verify(payload, TEST_KEY, WEBHOOK_SIGN)


def test_tricky_webhook_signature_matches_php_reference():
    payload = parse_webhook_body(TRICKY_WEBHOOK_BODY)
    assert Hmac.verify(payload, TEST_KEY, TRICKY_WEBHOOK_SIGN)


def test_parse_php_query_auto_index():
    """PHP parse_str: "key[]" получает индекс max(целые ключи) + 1."""
    parsed = parse_php_query(parse_qsl(
        'a[5]=y&a[]=z&a[2]=w&a[]=v', keep_blank_values=True
    ))
    assert parsed == {'a': {'5': 'y', '6': 'z', '2': 'w', '7': 'v'}}


def test_parse_php_query_last_key_wins_on_conflict():
    """PHP parse_str: при конфликте скаляра и массива побеждает поздний."""
    scalar_then_array = parse_php_query(parse_qsl('a=1&a[b]=2'))
    array_then_scalar = parse_php_query(parse_qsl('a[b]=1&a=2'))

    assert scalar_then_array == {'a': {'b': '2'}}
    assert array_then_scalar == {'a': '2'}


def test_http_build_query_flattens_nested_structures():
    query = http_build_query({'a': [{'b': 1}], 'c': 'x y'})

    assert 'a%5B0%5D%5Bb%5D=1' in query  # a[0][b]=1
    assert 'c=x+y' in query


def test_query_roundtrip_preserves_signature():
    """Вебхук приходит формой вида products[0][name]=...; после разбора
    подпись должна совпадать с подписью исходной структуры."""
    query = http_build_query(TEST_PAYLOAD)
    parsed = parse_php_query(parse_qsl(query, keep_blank_values=True))

    assert Hmac.verify(parsed, TEST_KEY, TEST_PAYLOAD_SIGN)


# --- Фазз-тест паритета с оригинальным PHP-классом Prodamus -----------------

# Класс Hmac из документации Prodamus (help.prodamus.ru, "Инструкции для
# самостоятельной интеграции сервисов") + обвязка: тело вебхука на stdin,
# ключ в argv[1], подпись на stdout
PHP_REFERENCE = r'''<?php
class Hmac
{
    static function create($data, $key, $algo = 'sha256')
    {
        if (!in_array($algo, hash_algos()))
            return false;

        self::_sort($data);
        array_walk_recursive($data, function(&$v){ $v = strval($v); });

        $data = json_encode($data, JSON_UNESCAPED_UNICODE);
        return hash_hmac($algo, $data, $key);
    }

    private static function _sort(&$data)
    {
        ksort($data, SORT_REGULAR);
        foreach ($data as &$arr)
            is_array($arr) && self::_sort($arr);
    }
}
parse_str(stream_get_contents(STDIN), $post);
echo Hmac::create($post, $argv[1]);
'''

FUZZ_VALUES = [
    '', '2850.00', '1', 'success', 'Успешная оплата',
    'https://t.me/AstroPulse_bot', '+79999999999', 'a b+c%20d',
    'кавычки "и" \\бэкслэш\\', 'line\nbreak\ttab', 'x/y/z', 'emoji 🌙',
    '0.00', '-5', '1e3', 'null', "'quote'", 'a=b&c', 'line\u2028sep\u2029end',
]
FUZZ_FIELDS = [
    'date', 'order_id', 'order_num', 'domain', 'sum', 'currency',
    'customer_phone', 'customer_email', 'customer_extra', 'payment_type',
    'commission', 'attempt', 'sys', 'payment_status',
    'payment_status_description',
]
FUZZ_PRODUCT_FIELDS = ['name', 'price', 'quantity', 'sum', 'paymentMethod']


def _random_webhook_body(rng: random.Random) -> str:
    pairs = [
        (field, rng.choice(FUZZ_VALUES))
        for field in rng.sample(FUZZ_FIELDS, rng.randint(3, len(FUZZ_FIELDS)))
    ]
    style = rng.random()
    for i in range(rng.randint(0, 12)):
        # последовательные индексы, с пропусками или автоиндекс "[]"
        idx = str(i) if style < 0.6 else (
            str(i * 2 + 1) if style < 0.8 else ''
        )
        for field in rng.sample(FUZZ_PRODUCT_FIELDS, rng.randint(1, 5)):
            pairs.append((f'products[{idx}][{field}]', rng.choice(FUZZ_VALUES)))

    return '&'.join(
        f'{quote_plus(key)}={quote_plus(value)}' for key, value in pairs
    )


@pytest.mark.skipif(
    not shutil.which('php'),
    reason='Нужен php в PATH для сверки с эталонной реализацией Prodamus'
)
def test_php_parity_fuzz(tmp_path):
    """Подпись случайных вебхуко-подобных тел должна байт-в-байт совпадать
    с подписью оригинального PHP-класса Prodamus."""
    reference = tmp_path / 'hmac_reference.php'
    reference.write_text(PHP_REFERENCE)

    rng = random.Random(20260711)
    for _ in range(150):
        body = _random_webhook_body(rng)

        php_sign = subprocess.run(
            ['php', str(reference), TEST_KEY],
            input=body.encode(), capture_output=True, check=True
        ).stdout.decode()

        payload = parse_webhook_body(body)
        assert Hmac.create(payload, TEST_KEY) == php_sign, body


@pytest.mark.skipif(
    not os.getenv('RUN_INTEGRATION_TESTS'),
    reason='Делает реальный запрос к Prodamus; включается '
           'переменной RUN_INTEGRATION_TESTS=1'
)
@pytest.mark.asyncio
async def test_payment_creation():
    payment = await ProdamusPaymentService.create_payment(
        months=6, user_id=1060062986
    )
    assert payment.payment_link
