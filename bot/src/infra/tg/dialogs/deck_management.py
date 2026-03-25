from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.services.deck import DeckService

from .common import get_dialog_data, get_user, make_on_create_deck_name, no_decks, on_back_to_menu
from .states import DeckManagementSG, ReviewSG


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
        to_review = stats["due"] + stats["new"]
        label = f"{d.name} ({stats['total']} картак, {to_review} да практыкі)"
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
    new = stats.get("new", 0)
    due = stats.get("due", 0)
    to_review = new + due
    return {
        "total": stats.get("total", 0),
        "new": new,
        "due": to_review,
        "has_due": to_review > 0,
    }


on_create_deck_name = make_on_create_deck_name(DeckManagementSG.list_decks)


async def on_start_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    deck_id: int | None = data.get("selected_deck_id")
    if deck_id is not None:
        await manager.start(ReviewSG.show_front, data={"deck_id": deck_id})  # pyright: ignore[reportUnknownMemberType]


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
            when=no_decks,
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
