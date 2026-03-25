from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo
from aiogram_dialog.widgets.text import Const
from dishka import AsyncContainer

from src.services.user import UserService

from .states import MainMenuSG, OnboardingSG


async def on_finish_onboarding(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    user = manager.middleware_data.get("user")
    if user:
        container: AsyncContainer = manager.middleware_data["dishka_container"]
        async with container() as request_container:
            user_service = await request_container.get(UserService)
            await user_service.complete_onboarding(user.id)

    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


onboarding_dialog = Dialog(
    Window(
        Const(
            "<b>Welcome to Slouka!</b>\n\n"
            "Your personal Belarusian vocabulary trainer.\n\n"
            "Build your word knowledge with flashcards "
            "powered by spaced repetition."
        ),
        SwitchTo(Const("Next →"), id="to_how", state=OnboardingSG.how_it_works),
        state=OnboardingSG.welcome,
    ),
    Window(
        Const(
            "<b>How it works</b>\n\n"
            "1. <b>Search</b> — Type any Belarusian word to look it up\n"
            "2. <b>Save</b> — Add words to your decks as flashcards\n"
            "3. <b>Review</b> — Practice with spaced repetition\n\n"
            "The system schedules reviews so you see words "
            "right before you'd forget them."
        ),
        SwitchTo(Const("Next →"), id="to_ready", state=OnboardingSG.ready),
        state=OnboardingSG.how_it_works,
    ),
    Window(
        Const("<b>You're all set!</b>\n\nLet's start by searching your first word."),
        Button(Const("Go to Menu →"), id="finish", on_click=on_finish_onboarding),
        state=OnboardingSG.ready,
    ),
)
