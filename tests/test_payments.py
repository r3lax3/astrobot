import os

import pytest

from urllib.parse import parse_qsl

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


def test_hmac_generation():
    assert Hmac.create(TEST_PAYLOAD, TEST_KEY, 'sha256') == TEST_PAYLOAD_SIGN


def test_hmac_verify():
    assert Hmac.verify(TEST_PAYLOAD, TEST_KEY, TEST_PAYLOAD_SIGN)
    assert not Hmac.verify(TEST_PAYLOAD, TEST_KEY, 'ff' * 32)
    assert not Hmac.verify(TEST_PAYLOAD, 'wrong-key', TEST_PAYLOAD_SIGN)


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
