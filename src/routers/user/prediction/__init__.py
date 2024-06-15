from aiogram import Router

from .every_day import r as every_day_router
from .on_date import r as on_date_router
from .day_selection import r as day_selection_router


r = Router()

all_routers = [on_date_router, every_day_router, day_selection_router]
r.include_routers(*all_routers)
