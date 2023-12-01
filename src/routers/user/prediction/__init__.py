from aiogram import Router

from src.routers.user.prediction.on_date import r as on_date_router
from src.routers.user.prediction.every_day import r as every_day_router

r = Router()

all_routers = [
    on_date_router,
    every_day_router
]
r.include_routers(*all_routers)

