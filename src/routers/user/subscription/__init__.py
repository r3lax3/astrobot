from aiogram import Router

from .buy_subscription import r as buy_subscription_router
from .promocode import r as promocode_router
from .menu import r as menu_router

r = Router()

all_routers = [
    menu_router,
    buy_subscription_router,
    promocode_router,
]
r.include_routers(*all_routers)
