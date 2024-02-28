import logging
import pytest

from src.payments import ProdamusPaymentService
from src.utils import Hmac


LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_payment_creation():
    test_data = [
        {"months": 6, "user_id": 1060062986}
    ]

    for kwargs in test_data:
        LOGGER.info(await ProdamusPaymentService.create_payment(**kwargs))

    assert True


def test_check_hmac_generation():
    data = {
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

    key = '63b90283bb6b538c4ae6ef17cbd158a8eb3c55f62d9f1c57d0a1b3b4c13c2a87'
    correct_sign = '8df73886bb4b2c24adce4eb8065862e895633f684f9f8863cca16794bc829b3d'

    sign = Hmac.create(data, key, 'sha256')
    assert sign == correct_sign
