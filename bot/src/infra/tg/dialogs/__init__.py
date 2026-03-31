from aiogram import Router

from .card_display import card_display_dialog
from .deck_management import deck_management_dialog
from .lookup import lookup_dialog
from .main_menu import main_menu_dialog
from .onboarding import onboarding_dialog
from .review import review_dialog
from .settings import settings_dialog


def get_dialogs_router() -> Router:
    router = Router()
    router.include_router(onboarding_dialog)
    router.include_router(main_menu_dialog)
    router.include_router(lookup_dialog)
    router.include_router(card_display_dialog)
    router.include_router(deck_management_dialog)
    router.include_router(review_dialog)
    router.include_router(settings_dialog)
    return router
