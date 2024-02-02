from aiogram import Router

from .about import r as about_router
from .birth import r as birth_router
from .card_of_day import r as card_of_day_router
from .compatibility import r as compatibility_router
from .dreams import r as dreams_router
from .general_predictions import r as general_predictions_router
from .main_menu import r as main_menu_router
from .moon_in_sign import r as moon_in_sign_router
from .not_implemented import r as not_implemented_router
from .prediction import r as prediction_router
from .profile_settings import r as profile_settings_router
from .start import r as start_router
from .subscription import r as subscription_router
from .support import r as support_router

r = Router()


all_routers = [
    main_menu_router,
    about_router,
    birth_router,
    card_of_day_router,
    compatibility_router,
    dreams_router,
    general_predictions_router,
    moon_in_sign_router,
    not_implemented_router,
    prediction_router,
    profile_settings_router,
    start_router,
    subscription_router,
    support_router,
]
r.include_routers(*all_routers)
