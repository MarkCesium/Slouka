from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.services.card import CardService
from src.services.deck import DeckService

from .common import get_dialog_data, get_user, make_on_create_deck_name, no_decks, on_back_to_menu
from .states import DeckManagementSG, ReviewSG

# ── Getters ──────────────────────────────────────────────────────────────────


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


async def deck_view_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    deck_name: str = data.get("deck_name", "")
    stats: dict[str, int] = data.get("deck_stats", {})
    new = stats.get("new", 0)
    due = stats.get("due", 0)
    to_review = new + due
    return {
        "deck_name": deck_name,
        "total": stats.get("total", 0),
        "new": new,
        "due": to_review,
        "has_due": to_review > 0,
    }


async def rename_deck_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    return {"deck_name": data.get("deck_name", "")}


async def confirm_delete_deck_getter(
    dialog_manager: DialogManager, **kwargs: Any
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    deck_name: str = data.get("deck_name", "")
    stats: dict[str, int] = data.get("deck_stats", {})
    return {"deck_name": deck_name, "total": stats.get("total", 0)}


@inject
async def cards_list_getter(
    dialog_manager: DialogManager,
    card_service: FromDishka[CardService],
    **kwargs: Any,
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    deck_id: int | None = data.get("selected_deck_id")
    deck_name: str = data.get("deck_name", "")

    if deck_id is None:
        return {"cards": [], "has_cards": False, "deck_name": deck_name}

    cards = await card_service.get_deck_cards(deck_id)
    card_items: list[tuple[str, str]] = [(c.word, str(c.id)) for c in cards]

    return {"cards": card_items, "has_cards": len(card_items) > 0, "deck_name": deck_name}


@inject
async def card_detail_getter(
    dialog_manager: DialogManager,
    card_service: FromDishka[CardService],
    **kwargs: Any,
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    card_id: int | None = data.get("selected_card_id")

    if card_id is None:
        return {"word": "", "definition": "", "examples": ""}

    card = await card_service.get_card_by_id(card_id)
    if not card:
        return {"word": "", "definition": "", "examples": ""}

    examples: str = card.examples or ""

    return {
        "word": card.word,
        "definition": card.definition,
        "examples": f"\n<i>{examples}</i>" if examples else "",
    }


async def confirm_delete_card_getter(
    dialog_manager: DialogManager, **kwargs: Any
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    return {"word": data.get("selected_card_word", "")}


# ── Callbacks ────────────────────────────────────────────────────────────────


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

    deck = await deck_service.get_deck_by_id(deck_id)
    if deck:
        data["deck_name"] = deck.name

    stats = await deck_service.get_deck_stats(deck_id)
    data["deck_stats"] = stats
    await manager.switch_to(DeckManagementSG.view_deck)


on_create_deck_name = make_on_create_deck_name(DeckManagementSG.list_decks)


async def on_start_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    deck_id: int | None = data.get("selected_deck_id")
    if deck_id is not None:
        await manager.start(ReviewSG.show_front, data={"deck_id": deck_id})  # pyright: ignore[reportUnknownMemberType]


@inject
async def on_rename_deck(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
    deck_service: FromDishka[DeckService],
) -> None:
    name = message.text
    if not name or not name.strip():
        await message.answer("Калі ласка, увядзіце новую назву калодкі.")
        return

    data = get_dialog_data(manager)
    deck_id: int | None = data.get("selected_deck_id")
    if deck_id is None:
        return

    await deck_service.rename_deck(deck_id, name.strip())
    data["deck_name"] = name.strip()

    stats = await deck_service.get_deck_stats(deck_id)
    data["deck_stats"] = stats
    await manager.switch_to(DeckManagementSG.view_deck)


@inject
async def on_delete_deck(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    deck_service: FromDishka[DeckService],
) -> None:
    data = get_dialog_data(manager)
    deck_id: int | None = data.get("selected_deck_id")
    if deck_id is not None:
        await deck_service.delete_deck(deck_id)
    await manager.switch_to(DeckManagementSG.list_decks)


@inject
async def on_card_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    card_service: FromDishka[CardService],
) -> None:
    card_id = int(item_id)
    data = get_dialog_data(manager)
    data["selected_card_id"] = card_id

    card = await card_service.get_card_by_id(card_id)
    if card:
        data["selected_card_word"] = card.word

    await manager.switch_to(DeckManagementSG.view_card)


@inject
async def on_reset_progress(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    card_service: FromDishka[CardService],
) -> None:
    data = get_dialog_data(manager)
    card_id: int | None = data.get("selected_card_id")
    if card_id is not None:
        await card_service.reset_card_progress(card_id)
    if callback.message:
        await callback.answer("Прагрэс скінуты", show_alert=True)


@inject
async def on_delete_card(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    card_service: FromDishka[CardService],
) -> None:
    data = get_dialog_data(manager)
    card_id: int | None = data.get("selected_card_id")
    if card_id is not None:
        await card_service.delete_card(card_id)
    await manager.switch_to(DeckManagementSG.view_cards)


def no_cards(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_cards")


# ── Dialog ───────────────────────────────────────────────────────────────────

deck_management_dialog = Dialog(
    # ── List decks ───────────────────────────────────────────────────────
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
    # ── Create deck ──────────────────────────────────────────────────────
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
    # ── View deck ────────────────────────────────────────────────────────
    Window(
        Format(
            "<b>{deck_name}</b>\n\n"
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
            Const("📋 Карткі"),
            id="cards",
            state=DeckManagementSG.view_cards,
        ),
        SwitchTo(
            Const("📝 Змяніць назву"),
            id="rename",
            state=DeckManagementSG.rename_deck,
        ),
        SwitchTo(
            Const("🗑 Выдаліць калодку"),
            id="delete",
            state=DeckManagementSG.confirm_delete_deck,
        ),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=DeckManagementSG.list_decks,
        ),
        state=DeckManagementSG.view_deck,
        getter=deck_view_getter,
    ),
    # ── Rename deck ──────────────────────────────────────────────────────
    Window(
        Format("<b>Змяніць назву калодкі</b>\n\nБягучая назва: {deck_name}\nУвядзіце новую назву:"),
        MessageInput(on_rename_deck),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=DeckManagementSG.view_deck,
        ),
        state=DeckManagementSG.rename_deck,
        getter=rename_deck_getter,
    ),
    # ── Confirm delete deck ──────────────────────────────────────────────
    Window(
        Format(
            '<b>Выдаліць калодку "{deck_name}"?</b>\n\n'
            "Усе карткі ({total}) будуць выдалены.\n"
            "Гэта дзеянне нельга адмяніць."
        ),
        Button(Const("🗑 Так, выдаліць"), id="confirm_delete", on_click=on_delete_deck),
        SwitchTo(
            Const("← Не, назад"),
            id="back",
            state=DeckManagementSG.view_deck,
        ),
        state=DeckManagementSG.confirm_delete_deck,
        getter=confirm_delete_deck_getter,
    ),
    # ── View cards list ──────────────────────────────────────────────────
    Window(
        Format("<b>Карткі ў калодцы «{deck_name}»</b>\n"),
        Select(
            Format("{item[0]}"),
            id="card_list",
            item_id_getter=lambda item: item[1],
            items="cards",
            on_click=on_card_selected,  # pyright: ignore[reportArgumentType]
        ),
        Const(
            "\nУ гэтай калодцы яшчэ няма картак.",
            when=no_cards,
        ),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=DeckManagementSG.view_deck,
        ),
        state=DeckManagementSG.view_cards,
        getter=cards_list_getter,
    ),
    # ── View card detail ─────────────────────────────────────────────────
    Window(
        Format("<b>{word}</b>\n\n{definition}{examples}"),
        Button(Const("🔄 Скінуць прагрэс"), id="reset", on_click=on_reset_progress),
        SwitchTo(
            Const("🗑 Выдаліць картку"),
            id="delete_card",
            state=DeckManagementSG.confirm_delete_card,
        ),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=DeckManagementSG.view_cards,
        ),
        state=DeckManagementSG.view_card,
        getter=card_detail_getter,
        parse_mode="HTML",
    ),
    # ── Confirm delete card ──────────────────────────────────────────────
    Window(
        Format('<b>Выдаліць картку "{word}"?</b>\n\nГэта дзеянне нельга адмяніць.'),
        Button(Const("🗑 Так, выдаліць"), id="confirm_delete_card", on_click=on_delete_card),
        SwitchTo(
            Const("← Не, назад"),
            id="back",
            state=DeckManagementSG.view_card,
        ),
        state=DeckManagementSG.confirm_delete_card,
        getter=confirm_delete_card_getter,
    ),
)
