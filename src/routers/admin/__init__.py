from aiogram import Router

from src.routers.admin.adminpanel import r as adminpanel_router
from src.routers.admin.broadcast import r as broadcast_router
from src.routers.admin.card_of_day import r as card_of_day_router
from src.routers.admin.general_predictions import \
    r as general_predictions_router
from src.routers.admin.statistics import r as statistics_router
from src.routers.admin.user_settings import r as user_settings_router

r = Router()

all_routers = [
    adminpanel_router,
    statistics_router,
    broadcast_router,
    user_settings_router,
    general_predictions_router,
    card_of_day_router,
]

r.include_routers(*all_routers)
