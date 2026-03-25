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

from .states import DeckManagementSG, MainMenuSG, ReviewSG

logger = logging.getLogger(__name__)


@inject
async def decks_list_getter(
    dialog_manager: DialogManager, deck_service: FromDishka[DeckService], **kwargs: Any
) -> dict[str, Any]:
    user = dialog_manager.middleware_data.get("user")
    if not user:
        return {"decks": [], "has_decks": False}

    decks = await deck_service.get_user_decks(user.id)
    deck_items = []
    for d in decks:
        stats = await deck_service.get_deck_stats(d.id)
        label = f"{d.name} ({stats['total']} cards, {stats['due']} due)"
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
    manager.dialog_data["selected_deck_id"] = deck_id

    stats = await deck_service.get_deck_stats(deck_id)

    manager.dialog_data["deck_stats"] = stats
    await manager.switch_to(DeckManagementSG.view_deck)


async def deck_view_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    stats = dialog_manager.dialog_data.get("deck_stats", {})
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
        await message.answer("Please enter a deck name.")
        return

    user = manager.middleware_data.get("user")
    if not user:
        return

    await deck_service.create_deck(user.id, name.strip())
    await manager.switch_to(DeckManagementSG.list_decks)


async def on_start_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    deck_id = manager.dialog_data.get("selected_deck_id")
    if deck_id:
        await manager.start(ReviewSG.show_front, data={"deck_id": deck_id})


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


deck_management_dialog = Dialog(
    Window(
        Const("<b>My Decks</b>\n"),
        Select(
            Format("{item[0]}"),
            id="deck_list",
            item_id_getter=lambda item: item[1],
            items="decks",
            on_click=on_deck_selected,
        ),
        Const("\nNo decks yet. Create one!", when=lambda data, *_: not data.get("has_decks")),
        SwitchTo(Const("➕ Create Deck"), id="create", state=DeckManagementSG.create_deck),
        Button(Const("← Menu"), id="menu", on_click=on_back_to_menu),
        state=DeckManagementSG.list_decks,
        getter=decks_list_getter,
    ),
    Window(
        Const("<b>Create New Deck</b>\n\nEnter deck name:"),
        MessageInput(on_create_deck_name),
        SwitchTo(Const("← Back"), id="back", state=DeckManagementSG.list_decks),
        state=DeckManagementSG.create_deck,
    ),
    Window(
        Format(
            "<b>Deck Details</b>\n\nTotal cards: {total}\nNew cards: {new}\nDue for review: {due}"
        ),
        Button(
            Const("🧠 Start Review"),
            id="review",
            on_click=on_start_review,
            when="has_due",
        ),
        SwitchTo(Const("← Back"), id="back", state=DeckManagementSG.list_decks),
        state=DeckManagementSG.view_deck,
        getter=deck_view_getter,
    ),
)
