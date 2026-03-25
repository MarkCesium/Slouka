import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import AsyncContainer

from src.infra.schemas.verbum import ParsedCard
from src.services.card import CardService
from src.services.deck import DeckService

from .states import CardDisplaySG, MainMenuSG

logger = logging.getLogger(__name__)


async def decks_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    user = dialog_manager.middleware_data.get("user")
    if not user:
        return {"decks": [], "has_decks": False}

    container: AsyncContainer = dialog_manager.middleware_data["dishka_container"]
    async with container() as request_container:
        deck_service = await request_container.get(DeckService)
        decks = await deck_service.get_user_decks(user.id)

    return {
        "decks": [(d.name, str(d.id)) for d in decks],
        "has_decks": len(decks) > 0,
    }


async def on_deck_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
) -> None:
    deck_id = int(item_id)
    start_data = manager.start_data or {}
    card_data = start_data.get("parsed_card", {}) if isinstance(start_data, dict) else {}

    if not card_data:
        await callback.answer("Error: no card data.")
        return

    parsed_card = ParsedCard.model_validate(card_data)

    container: AsyncContainer = manager.middleware_data["dishka_container"]
    async with container() as request_container:
        card_service = await request_container.get(CardService)
        result = await card_service.create_card(deck_id, parsed_card)

    if result is None:
        await callback.answer("This word is already in this deck!", show_alert=True)
        return

    manager.dialog_data["added_word"] = parsed_card.headword
    await manager.switch_to(CardDisplaySG.added)


async def on_create_deck_name(
    message: Message, widget: MessageInput, manager: DialogManager
) -> None:
    name = message.text
    if not name or not name.strip():
        await message.answer("Please enter a deck name.")
        return

    user = manager.middleware_data.get("user")
    if not user:
        return

    container: AsyncContainer = manager.middleware_data["dishka_container"]
    async with container() as request_container:
        deck_service = await request_container.get(DeckService)
        await deck_service.create_deck(user.id, name.strip())

    await manager.switch_to(CardDisplaySG.select_deck)


async def added_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    word = dialog_manager.dialog_data.get("added_word", "")
    return {"word": word}


async def on_back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


async def on_done(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.done()


card_display_dialog = Dialog(
    Window(
        Const("<b>Select a deck:</b>"),
        Select(
            Format("{item[0]}"),
            id="deck_select",
            item_id_getter=lambda item: item[1],
            items="decks",
            on_click=on_deck_selected,
        ),
        Const("\nNo decks yet. Create one!", when=lambda data, *_: not data.get("has_decks")),
        SwitchTo(
            Const("➕ Create Deck"), id="create", state=CardDisplaySG.create_deck
        ),
        Button(Const("← Back"), id="back", on_click=on_done),
        state=CardDisplaySG.select_deck,
        getter=decks_getter,
    ),
    Window(
        Const("<b>Create New Deck</b>\n\nEnter deck name:"),
        MessageInput(on_create_deck_name),
        SwitchTo(Const("← Back"), id="back", state=CardDisplaySG.select_deck),
        state=CardDisplaySG.create_deck,
    ),
    Window(
        Format("Card <b>{word}</b> added to deck!"),
        Button(Const("← Menu"), id="menu", on_click=on_back_to_menu),
        Button(Const("← Back to results"), id="back_results", on_click=on_done),
        state=CardDisplaySG.added,
        getter=added_getter,
    ),
)
