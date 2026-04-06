from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, SwitchTo
from aiogram_dialog.widgets.text import Const
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.infra.tg.strings import Onboarding
from src.services.user import UserService

from .common import get_user
from .states import MainMenuSG, OnboardingSG


@inject
async def on_finish_onboarding(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if user:
        await user_service.complete_onboarding(user.id)

    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)  # pyright: ignore[reportUnknownMemberType]


onboarding_dialog = Dialog(
    Window(
        Const(Onboarding.WELCOME),
        SwitchTo(Const(Onboarding.NEXT), id="to_how", state=OnboardingSG.how_it_works),
        state=OnboardingSG.welcome,
    ),
    Window(
        Const(Onboarding.HOW_IT_WORKS),
        SwitchTo(Const(Onboarding.NEXT), id="to_ready", state=OnboardingSG.ready),
        state=OnboardingSG.how_it_works,
    ),
    Window(
        Const(Onboarding.READY),
        Button(Const(Onboarding.GO_TO_MENU), id="finish", on_click=on_finish_onboarding),
        state=OnboardingSG.ready,
    ),
)
