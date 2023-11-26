from aiogram import Router

from src.routers.user.about import r as about_router
from src.routers.user.birth import r as birth_router
from src.routers.user.card_of_day import r as card_of_day_router
from src.routers.user.compatibility import r as compatibility_router
from src.routers.user.general_predictions import r as general_predictions_router
from src.routers.user.main_menu import r as main_menu_router
from src.routers.user.moon_in_sign import r as moon_in_sign_router
from src.routers.user.not_implemented import r as not_implemented_router
from src.routers.user.prediction import r as prediction_router
from src.routers.user.profile_settings import r as profile_settings_router
from src.routers.user.start import r as start_router
from src.routers.user.subsription import r as subsription_router
from src.routers.user.technical_support import r as technical_support_router


r = Router()


# The main router for the Telegram bot, integrating various sub-routers
all_routers = [
    about_router,
    birth_router,
    card_of_day_router,
    compatibility_router,
    general_predictions_router,
    main_menu_router,
    moon_in_sign_router,
    not_implemented_router,
    prediction_router,
    profile_settings_router,
    start_router,
    subsription_router,
    technical_support_router
]
r.include_routers(
    *all_routers
)

