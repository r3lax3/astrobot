import logging
import aiohttp

from datetime import datetime, timedelta
from typing import Protocol

from aiohttp import web

from src import config, messages
from src.common import bot
from src.keyboards import keyboards
from src.database import crud
from src.database.models import Promocode
from src.enums import PaymentStatus
from src.dicts import MONTHS_TO_RUB_PRICE, MONTHS_TO_STR_MONTHS
from src.models import Payment, SubscriptionItem
from src.payments.utils import Hmac, http_build_query, parse_php_query


LOGGER = logging.getLogger(__name__)


DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
PAYMENT_LINK_TTL_HOURS = 48

PRODAMUS_PAYMENT_LINK = config.get("payments.prodamus_payment_link")
PRODAMUS_SECRET_KEY = config.get("payments.prodamus_secret_key")
# Флаг на случай, если Prodamus изменит формат подписи: позволяет
# отключить проверку, не выкатывая новый код.
VERIFY_WEBHOOK_SIGNATURE = config.get(
    "payments.verify_webhook_signature", default=True
)

# Куда Prodamus отправляет пользователя после успешной оплаты
PAID_CONTENT_URL = config.get(
    "payments.paid_content_url",
    default=f"https://t.me/{config.get('bot.username')}"
)


class PaymentService(Protocol):
    async def create_payment_link(self, months: int, user_id: int) -> str:
        pass

    @staticmethod
    async def get_payment_status(payment_id: str) -> PaymentStatus:
        pass


class ProdamusPaymentService(PaymentService):
    @staticmethod
    async def create_payment(months: int, user_id: int) -> Payment:
        link_expiry_utc = datetime.utcnow() + timedelta(
            hours=PAYMENT_LINK_TTL_HOURS
        )
        payment_id = crud.get_not_occupied_payment_id()

        price = MONTHS_TO_RUB_PRICE[months]

        params = {
            'do': 'link',
            'products': [
                {
                    'name': f"Подписка на Астропульс, {MONTHS_TO_STR_MONTHS[months]}",
                    'price': price,
                    'quantity': 1,
                    'paymentMethod': 4,
                    'paymentObject': 4,
                }
            ],
            'link_expired': link_expiry_utc.strftime(DEFAULT_DATETIME_FORMAT),
            'order_id': payment_id,
            'sys': '',
            'paid_content': PAID_CONTENT_URL,
            'acquiring': "sbrf"
        }

        params['signature'] = Hmac.create(params, PRODAMUS_SECRET_KEY)

        url = f"{PRODAMUS_PAYMENT_LINK}?{http_build_query(params)}"

        LOGGER.info(f'Payment url is generated: {url}')

        async with aiohttp.request(method='GET', url=url) as resp:
            return Payment(
                id=payment_id,
                payment_link=await resp.text(),
                price=price
            )

    @staticmethod
    async def handle_payment_update(request: web.Request) -> web.Response:
        data = await request.post()

        if VERIFY_WEBHOOK_SIGNATURE:
            # Как в эталонном PHP-приёмнике Prodamus: подпись берётся из
            # заголовка Sign, проверяется всё тело запроса целиком
            signature = request.headers.get('Sign', '')
            payload = parse_php_query(data.items())

            if not Hmac.verify(payload, PRODAMUS_SECRET_KEY, signature):
                LOGGER.warning('Payment webhook: invalid signature, rejected')
                return web.Response(status=401)

        payment_id = data.get("order_num")
        payment_status = data.get("payment_status")

        if payment_status != 'success':
            return web.Response(status=400)

        crud.update_payment(
            payment_id=payment_id,
            status=payment_status,
            status_change_timestamp=datetime.utcnow().strftime(DEFAULT_DATETIME_FORMAT)
        )

        payment = crud.get_payment(payment_id)
        months = SubscriptionItem.unpack(payment.item).months

        promocode = payment_id
        crud.add_promocode(
            Promocode(
                promocode=promocode,
                activated_by=None,
                is_activated=False,
                period=months,
            )
        )
        await bot.send_message(
            chat_id=payment.user_id,
            text=messages.YOUR_PROMOCODE_IS.format(promocode=promocode)
        )
        await bot.send_message(
            chat_id=payment.user_id,
            text=messages.PAYMENT_SUCCESS,
            reply_markup=keyboards.payment_success(promocode)
        )

        return web.Response(status=200)
