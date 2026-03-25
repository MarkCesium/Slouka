import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.services.deck import DeckService

from .common import get_dialog_data, get_user
from .states import DeckManagementSG, MainMenuSG, ReviewSG

logger = logging.getLogger(__name__)


@inject
async def decks_list_getter(
    dialog_manager: DialogManager,
    deck_service: FromDishka[DeckService],
    **kwargs: Any,
) -> dict[str, Any]:
    user = get_user(dialog_manager)
    if not user:
        return {"decks": [], "has_decks": False}

    decks = await deck_service.get_user_decks(user.id)
    deck_items: list[tuple[str, str]] = []
    for d in decks:
        stats = await deck_service.get_deck_stats(d.id)
        label = f"{d.name} ({stats['total']} картак, {stats['due']} да практыкі)"
        deck_items.append((label, str(d.id)))

    return {"decks": deck_items, "has_decks": len(deck_items) > 0}


@inject
async def on_deck_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    deck_service: FromDishka[DeckService],
) -> None:
    deck_id = int(item_id)
    data = get_dialog_data(manager)
    data["selected_deck_id"] = deck_id

    stats = await deck_service.get_deck_stats(deck_id)

    data["deck_stats"] = stats
    await manager.switch_to(DeckManagementSG.view_deck)


async def deck_view_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    stats: dict[str, int] = data.get("deck_stats", {})
    return {
        "total": stats.get("total", 0),
        "new": stats.get("new", 0),
        "due": stats.get("due", 0),
        "has_due": stats.get("due", 0) > 0 or stats.get("new", 0) > 0,
    }


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
    await manager.switch_to(DeckManagementSG.list_decks)


async def on_start_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    deck_id: int | None = data.get("selected_deck_id")
    if deck_id is not None:
        await manager.start(ReviewSG.show_front, data={"deck_id": deck_id})


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


def _no_decks(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_decks")


deck_management_dialog = Dialog(
    Window(
        Const("<b>Мае калодкі</b>\n"),
        Select(
            Format("{item[0]}"),
            id="deck_list",
            item_id_getter=lambda item: item[1],
            items="decks",
            on_click=on_deck_selected,  # pyright: ignore[reportArgumentType]
        ),
        Const(
            "\nЯшчэ няма калодак. Стварыце новую!",
            when=_no_decks,
        ),
        SwitchTo(
            Const("➕ Стварыць калодку"),
            id="create",
            state=DeckManagementSG.create_deck,
        ),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        state=DeckManagementSG.list_decks,
        getter=decks_list_getter,
    ),
    Window(
        Const("<b>Стварыць новую калодку</b>\n\nУвядзіце назву калодкі:"),
        MessageInput(on_create_deck_name),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=DeckManagementSG.list_decks,
        ),
        state=DeckManagementSG.create_deck,
    ),
    Window(
        Format(
            "<b>Дэталі калодкі</b>\n\n"
            "Агульная колькасць картак: {total}\n"
            "Новыя карткі: {new}\n"
            "Да практыкі: {due}"
        ),
        Button(
            Const("🧠 Пачаць практыку"),
            id="review",
            on_click=on_start_review,
            when="has_due",
        ),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=DeckManagementSG.list_decks,
        ),
        state=DeckManagementSG.view_deck,
        getter=deck_view_getter,
    ),
)
