import logging
import aiohttp

from datetime import datetime, timedelta
from typing import Protocol

from php import Php
from aiohttp import web

from src import config, messages
from src.common import bot
from src.keyboards import keyboards
from src.database import crud
from src.database.models import Promocode
from src.enums import PaymentStatus
from src.dicts import MONTHS_TO_RUB_PRICE, MONTHS_TO_STR_MONTHS
from src.utils import Hmac
from src.models import Payment, SubscriptionItem


LOGGER = logging.getLogger(__name__)


DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
RETURN_URL = "https://t.me/AstroPulse_bot"

# YOOKASSA_TOKEN = config.get("payments.yookassa_token")
# YOOKASSA_SHOP_ID = config.get("payments.yookassa_shop_id")

PRODAMUS_PAYMENT_LINK = config.get("payments.prodamus_payment_link")
PRODAMUS_SECRET_KEY = config.get("payments.prodamus_secret_key")

# Configuration.account_id = YOOKASSA_SHOP_ID
# Configuration.secret_key = YOOKASSA_TOKEN


class PaymentService(Protocol):
    async def create_payment_link(self, months: int, user_id: int) -> str:
        pass

    @staticmethod
    async def get_payment_status(payment_id: str) -> PaymentStatus:
        pass


class ProdamusPaymentService(PaymentService):
    @staticmethod
    async def create_payment(months: int, user_id: int) -> Payment:
        now_utc = datetime.utcnow()
        six_hours_later_utc = now_utc + timedelta(hours=48)
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
            'link_expired': six_hours_later_utc.strftime(DEFAULT_DATETIME_FORMAT),
            'order_id': payment_id,
            'sys': '',
            'paid_content': 'https://t.me/AstroPulse_bot',
            'acquiring': "sbrf"
        }

        signature = Hmac.create(params, PRODAMUS_SECRET_KEY)
        params['signature'] = signature

        query = Php.http_build_query(params)
        url = PRODAMUS_PAYMENT_LINK + f"?{query}"

        LOGGER.info(f'Payment url is generated: {url}')

        async with aiohttp.request(method='GET', url=url) as resp:
            return Payment(
                id=payment_id,
                payment_link=await resp.text(),
                price=price
            )

    @staticmethod
    async def handle_payment_update(request):
        data = await request.post()

        payment_id = data.get("order_num")
        payment_status = data.get("payment_status")

        if not payment_status == 'success':
            return web.Response(status=400)

        crud.update_payment(payment_id=payment_id, status=payment_status)

        payment = crud.get_payment(payment_id)
        months = SubscriptionItem.unpack(payment.item).months

        promocode = crud.get_not_occupied_promocode()
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


# class YookassaPaymentService(PaymentService):
#     @staticmethod
#     async def create_payment(months: int, user_id: int) -> Payment:
#         price = MONTHS_TO_RUB_PRICE[months]
#         months_str = MONTHS_TO_STR_MONTHS[months]
#
#         idempotence_key = str(uuid.uuid4())
#
#         utcnow = datetime.utcnow()
#         delta_6_hours_after_utcnow = utcnow + timedelta(hours=6)
#
#         payment_auto_cancel = delta_6_hours_after_utcnow.replace(microsecond=0)
#         payment_auto_cancel_str = payment_auto_cancel.isoformat() + "Z"
#
#         yokassa_payment = YookassaPayment.create(
#             {
#                 "amount": {
#                     "value": f"{price}",
#                     "currency": "RUB"
#                 },
#                 "confirmation": {
#                     "type": "redirect",
#                     "return_url": RETURN_URL
#                 },
#                 "capture": False,
#                 "expires_at": payment_auto_cancel_str,
#                 "description": f"Подписка на АстроПульс, {months_str}",
#             },
#             idempotence_key
#         )
#
#         return Payment(
#             id=yokassa_payment.id,
#             redirect_link=yokassa_payment.confirmation.confirmation_url
#         )
#
#     @abstractmethod
#     async def get_payment_status(payment_id: str) -> PaymentStatus:
#         pass
#
#     @abstractmethod
#     async def success():
#         pass
#
#     @abstractmethod
#     async def fail():
#         pass
#
#     @abstractmethod
#     async def pending():
#         pass
