import logging
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.services.card import CardService
from src.services.deck import DeckService

from .common import get_dialog_data, get_start_data, get_user
from .states import MainMenuSG, ReviewSG

logger = logging.getLogger(__name__)


@inject
async def select_deck_getter(
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
        due_count = stats["due"] + stats["new"]
        if due_count > 0:
            label = f"{d.name} ({due_count} да практыкі)"
            deck_items.append((label, str(d.id)))

    return {"decks": deck_items, "has_decks": len(deck_items) > 0}


@inject
async def on_review_deck_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    card_service: FromDishka[CardService],
) -> None:
    deck_id = int(item_id)
    data = get_dialog_data(manager)
    data["deck_id"] = deck_id
    await _load_review_cards(manager, card_service, deck_id)

    if data.get("card_ids"):
        await manager.switch_to(ReviewSG.show_front)
    else:
        await callback.answer("Няма картак для практыкі ў гэтай калодцы.")


async def _load_review_cards(
    manager: DialogManager, card_service: CardService, deck_id: int
) -> None:
    cards = await card_service.get_due_cards(deck_id)
    data = get_dialog_data(manager)

    data["card_ids"] = [c.id for c in cards]
    data["card_index"] = 0
    data["reviewed_count"] = 0
    data["total_count"] = len(cards)


async def _get_current_card(
    manager: DialogManager, card_service: CardService
) -> dict[str, Any] | None:
    data = get_dialog_data(manager)
    card_ids: list[int] = data.get("card_ids", [])
    index: int = data.get("card_index", 0)

    if index >= len(card_ids):
        return None

    card_id = card_ids[index]
    card = await card_service.get_card_by_id(card_id)

    if not card:
        return None

    return {
        "id": card.id,
        "word": card.word,
        "definition": card.definition,
        "examples": card.examples,
    }


@inject
async def front_getter(
    dialog_manager: DialogManager,
    card_service: FromDishka[CardService],
    **kwargs: Any,
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    start = get_start_data(dialog_manager)
    if not data.get("card_ids") and start:
        deck_id: int | None = start.get("deck_id")
        if deck_id is not None:
            await _load_review_cards(dialog_manager, card_service, deck_id)

    card = await _get_current_card(dialog_manager, card_service)
    if not card:
        return {"word": "Няма картак для практыкі.", "progress": ""}

    total: int = data.get("total_count", 0)
    reviewed: int = data.get("reviewed_count", 0)

    return {
        "word": card["word"],
        "progress": f"Картка {reviewed + 1} з {total}",
    }


@inject
async def back_getter(
    dialog_manager: DialogManager,
    card_service: FromDishka[CardService],
    **kwargs: Any,
) -> dict[str, Any]:
    card = await _get_current_card(dialog_manager, card_service)
    if not card:
        return {"word": "", "definition": "", "examples": ""}

    examples: str = card.get("examples") or ""

    return {
        "word": card["word"],
        "definition": card["definition"],
        "examples": f"\n<i>{examples}</i>" if examples else "",
    }


async def on_show_answer(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.switch_to(ReviewSG.show_back)


async def _rate_card(
    manager: DialogManager,
    card_service: CardService,
    quality: int,
) -> None:
    data = get_dialog_data(manager)
    card_ids: list[int] = data.get("card_ids", [])
    index: int = data.get("card_index", 0)

    if index < len(card_ids):
        card_id = card_ids[index]
        await card_service.review_card(card_id, quality)

    data["card_index"] = index + 1
    data["reviewed_count"] = int(data.get("reviewed_count", 0)) + 1

    if data["card_index"] >= len(card_ids):
        await manager.switch_to(ReviewSG.session_complete)
    else:
        await manager.switch_to(ReviewSG.show_front)


@inject
async def on_again(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    card_service: FromDishka[CardService],
) -> None:
    await _rate_card(manager, card_service, quality=0)


@inject
async def on_hard(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    card_service: FromDishka[CardService],
) -> None:
    await _rate_card(manager, card_service, quality=2)


@inject
async def on_good(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    card_service: FromDishka[CardService],
) -> None:
    await _rate_card(manager, card_service, quality=4)


@inject
async def on_easy(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    card_service: FromDishka[CardService],
) -> None:
    await _rate_card(manager, card_service, quality=5)


async def complete_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    reviewed: int = data.get("reviewed_count", 0)
    return {"reviewed": reviewed}


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


def _no_decks(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_decks")


review_dialog = Dialog(
    Window(
        Const("<b>Абярыце калодку для практыкі:</b>"),
        Select(
            Format("{item[0]}"),
            id="review_deck",
            item_id_getter=lambda item: item[1],
            items="decks",
            on_click=on_review_deck_selected,  # pyright: ignore[reportArgumentType]
        ),
        Const(
            "\nНяма калодак з карткамі для практыкі.",
            when=_no_decks,
        ),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        state=ReviewSG.select_deck,
        getter=select_deck_getter,
    ),
    Window(
        Format("<b>{word}</b>"),
        Format("\n{progress}"),
        Button(Const("Паказаць адказ"), id="show", on_click=on_show_answer),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        state=ReviewSG.show_front,
        getter=front_getter,
    ),
    Window(
        Format("<b>{word}</b>\n\n{definition}{examples}"),
        Const("\n\nЯк добра вы ведаеце гэтае слова?"),
        Group(
            Row(
                Button(Const("Дрэнна"), id="again", on_click=on_again),
                Button(Const("Цяжка"), id="hard", on_click=on_hard),
                Button(Const("Нармалёва"), id="good", on_click=on_good),
                Button(Const("Лёгка"), id="easy", on_click=on_easy),
            ),
        ),
        state=ReviewSG.show_back,
        getter=back_getter,
        parse_mode="HTML",
    ),
    Window(
        Format("<b>Практыка завершана!</b>\n\nВы праглядзелі {reviewed} картку(і)."),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        state=ReviewSG.session_complete,
        getter=complete_getter,
    ),
)
