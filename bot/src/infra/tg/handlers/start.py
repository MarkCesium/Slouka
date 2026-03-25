from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.infra.db.models import User
from src.infra.tg.dialogs.states import MainMenuSG, OnboardingSG

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, dialog_manager: DialogManager, **kwargs: object) -> None:
    user = kwargs.get("user")

    if not isinstance(user, User) or not user.onboarding_completed:
        await dialog_manager.start(OnboardingSG.welcome, mode=StartMode.RESET_STACK)  # pyright: ignore[reportUnknownMemberType]
    else:
        await dialog_manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)  # pyright: ignore[reportUnknownMemberType]
