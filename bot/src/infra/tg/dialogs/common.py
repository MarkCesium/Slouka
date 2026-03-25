from collections.abc import Callable
from typing import Any

from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.infra.db.models import User
from src.services.deck import DeckService

from .states import MainMenuSG

_ManagerAny = Any


def get_dialog_data(manager: DialogManager) -> dict[str, Any]:
    m: _ManagerAny = manager
    result: dict[str, Any] = m.dialog_data
    return result


def get_start_data(manager: DialogManager) -> dict[str, Any]:
    m: _ManagerAny = manager
    data: Any = m.start_data
    if isinstance(data, dict):
        result: dict[str, Any] = data  # pyright: ignore[reportUnknownVariableType]
        return result
    return {}


def get_user(manager: DialogManager) -> User | None:
    m: _ManagerAny = manager
    data: dict[str, Any] = m.middleware_data
    user = data.get("user")
    if isinstance(user, User):
        return user
    return None


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)  # pyright: ignore[reportUnknownMemberType]


def no_decks(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_decks")


def make_on_create_deck_name(
    target_state: State,
) -> Callable[..., Any]:
    @inject
    async def on_create_deck_name(
        message: Message,
        widget: MessageInput,
        manager: DialogManager,
        deck_service: FromDishka[DeckService],
    ) -> None:
        name = message.text
        if not name or not name.strip():
            await message.answer("Калі ласка, увядзіце назву калодкі.")
            return

        user = get_user(manager)
        if not user:
            return

        await deck_service.create_deck(user.id, name.strip())
        await manager.switch_to(target_state)  # pyright: ignore[reportUnknownMemberType]

    return on_create_deck_name
