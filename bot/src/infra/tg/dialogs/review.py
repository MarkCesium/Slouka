import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import AsyncContainer

from src.services.card import CardService
from src.services.deck import DeckService

from .states import MainMenuSG, ReviewSG

logger = logging.getLogger(__name__)


async def select_deck_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    user = dialog_manager.middleware_data.get("user")
    if not user:
        return {"decks": [], "has_decks": False}

    container: AsyncContainer = dialog_manager.middleware_data["dishka_container"]
    async with container() as request_container:
        deck_service = await request_container.get(DeckService)
        decks = await deck_service.get_user_decks(user.id)
        deck_items = []
        for d in decks:
            stats = await deck_service.get_deck_stats(d.id)
            due_count = stats["due"] + stats["new"]
            if due_count > 0:
                label = f"{d.name} ({due_count} to review)"
                deck_items.append((label, str(d.id)))

    return {"decks": deck_items, "has_decks": len(deck_items) > 0}


async def on_review_deck_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
) -> None:
    deck_id = int(item_id)
    manager.dialog_data["deck_id"] = deck_id
    await _load_review_cards(manager, deck_id)

    if manager.dialog_data.get("card_ids"):
        await manager.switch_to(ReviewSG.show_front)
    else:
        await callback.answer("No cards to review!")


async def _load_review_cards(manager: DialogManager, deck_id: int) -> None:
    container: AsyncContainer = manager.middleware_data["dishka_container"]
    async with container() as request_container:
        card_service = await request_container.get(CardService)
        cards = await card_service.get_due_cards(deck_id)

    manager.dialog_data["card_ids"] = [c.id for c in cards]
    manager.dialog_data["card_index"] = 0
    manager.dialog_data["reviewed_count"] = 0
    manager.dialog_data["total_count"] = len(cards)


async def _get_current_card(manager: DialogManager) -> dict[str, Any] | None:
    card_ids = manager.dialog_data.get("card_ids", [])
    index = manager.dialog_data.get("card_index", 0)

    if index >= len(card_ids):
        return None

    card_id = card_ids[index]
    container: AsyncContainer = manager.middleware_data["dishka_container"]
    async with container() as request_container:
        card_service = await request_container.get(CardService)
        card = await card_service.get_card_by_id(card_id)

    if not card:
        return None

    return {
        "id": card.id,
        "word": card.word,
        "definition": card.definition,
        "examples": card.examples,
    }


async def front_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    # If started with deck_id in data, load cards first
    start_data = dialog_manager.start_data
    if not dialog_manager.dialog_data.get("card_ids") and isinstance(start_data, dict):
        deck_id = start_data.get("deck_id")
        if deck_id:
            await _load_review_cards(dialog_manager, deck_id)

    card = await _get_current_card(dialog_manager)
    if not card:
        return {"word": "No cards to review", "progress": ""}

    total = dialog_manager.dialog_data.get("total_count", 0)
    reviewed = dialog_manager.dialog_data.get("reviewed_count", 0)

    return {
        "word": card["word"],
        "progress": f"Card {reviewed + 1} of {total}",
    }


async def back_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    card = await _get_current_card(dialog_manager)
    if not card:
        return {"word": "", "definition": "", "examples": ""}

    examples = card.get("examples") or ""

    return {
        "word": card["word"],
        "definition": card["definition"],
        "examples": f"\n<i>{examples}</i>" if examples else "",
    }


async def on_show_answer(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(ReviewSG.show_back)


async def _rate_card(callback: CallbackQuery, manager: DialogManager, quality: int) -> None:
    card_ids = manager.dialog_data.get("card_ids", [])
    index = manager.dialog_data.get("card_index", 0)

    if index < len(card_ids):
        card_id = card_ids[index]
        container: AsyncContainer = manager.middleware_data["dishka_container"]
        async with container() as request_container:
            card_service = await request_container.get(CardService)
            await card_service.review_card(card_id, quality)

    manager.dialog_data["card_index"] = index + 1
    manager.dialog_data["reviewed_count"] = manager.dialog_data.get("reviewed_count", 0) + 1

    if manager.dialog_data["card_index"] >= len(card_ids):
        await manager.switch_to(ReviewSG.session_complete)
    else:
        await manager.switch_to(ReviewSG.show_front)


async def on_again(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _rate_card(callback, manager, quality=0)


async def on_hard(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _rate_card(callback, manager, quality=2)


async def on_good(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _rate_card(callback, manager, quality=4)


async def on_easy(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await _rate_card(callback, manager, quality=5)


async def complete_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    reviewed = dialog_manager.dialog_data.get("reviewed_count", 0)
    return {"reviewed": reviewed}


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


review_dialog = Dialog(
    Window(
        Const("<b>Select a deck to review:</b>"),
        Select(
            Format("{item[0]}"),
            id="review_deck",
            item_id_getter=lambda item: item[1],
            items="decks",
            on_click=on_review_deck_selected,
        ),
        Const("\nNo decks with cards to review.", when=lambda data, *_: not data.get("has_decks")),
        Button(Const("← Menu"), id="menu", on_click=on_back_to_menu),
        state=ReviewSG.select_deck,
        getter=select_deck_getter,
    ),
    Window(
        Format("<b>{word}</b>"),
        Format("\n{progress}"),
        Button(Const("Show Answer"), id="show", on_click=on_show_answer),
        Button(Const("← Menu"), id="menu", on_click=on_back_to_menu),
        state=ReviewSG.show_front,
        getter=front_getter,
    ),
    Window(
        Format("<b>{word}</b>\n\n{definition}{examples}"),
        Const("\n\nHow well did you know this?"),
        Group(
            Row(
                Button(Const("Again"), id="again", on_click=on_again),
                Button(Const("Hard"), id="hard", on_click=on_hard),
                Button(Const("Good"), id="good", on_click=on_good),
                Button(Const("Easy"), id="easy", on_click=on_easy),
            ),
        ),
        state=ReviewSG.show_back,
        getter=back_getter,
        parse_mode="HTML",
    ),
    Window(
        Format("<b>Review Complete!</b>\n\nYou reviewed {reviewed} card(s).\nGreat job! 🎉"),
        Button(Const("← Menu"), id="menu", on_click=on_back_to_menu),
        state=ReviewSG.session_complete,
        getter=complete_getter,
    ),
)
