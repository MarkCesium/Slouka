import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.infra.schemas.verbum import ParsedCard
from src.services.card import CardService
from src.services.deck import DeckService

from .common import get_dialog_data, get_start_data, get_user
from .states import CardDisplaySG, MainMenuSG

logger = logging.getLogger(__name__)


@inject
async def decks_getter(
    dialog_manager: DialogManager,
    deck_service: FromDishka[DeckService],
    **kwargs: Any,
) -> dict[str, Any]:
    user = get_user(dialog_manager)
    if not user:
        return {"decks": [], "has_decks": False}

    decks = await deck_service.get_user_decks(user.id)

    return {
        "decks": [(d.name, str(d.id)) for d in decks],
        "has_decks": len(decks) > 0,
    }


@inject
async def on_deck_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    card_service: FromDishka[CardService],
) -> None:
    deck_id = int(item_id)
    start = get_start_data(manager)
    card_data: dict[str, Any] = start.get("parsed_card", {})

    if not card_data:
        await callback.answer("Памылка: няма даных карткі.")
        return

    parsed_card = ParsedCard.model_validate(card_data)
    result = await card_service.create_card(deck_id, parsed_card)

    if result is None:
        await callback.answer(
            "Гэтае слова ўжо ёсць у гэтай калодке!",
            show_alert=True,
        )
        return

    data = get_dialog_data(manager)
    data["added_word"] = parsed_card.headword
    await manager.switch_to(CardDisplaySG.added)


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
    await manager.switch_to(CardDisplaySG.select_deck)


async def added_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    word: str = data.get("added_word", "")
    return {"word": word}


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK) # pyright: ignore[reportUnknownMemberType]


async def on_done(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.done()


def _no_decks(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_decks")


card_display_dialog = Dialog(
    Window(
        Const("<b>Абярыце калодку:</b>"),
        Select(
            Format("{item[0]}"),
            id="deck_select",
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
            state=CardDisplaySG.create_deck,
        ),
        Button(Const("← Назад"), id="back", on_click=on_done),
        state=CardDisplaySG.select_deck,
        getter=decks_getter,
    ),
    Window(
        Const("<b>Стварыць новую калодку</b>\n\nУвядзіце назву калодкі:"),
        MessageInput(on_create_deck_name),
        SwitchTo(
            Const("← Назад"),
            id="back",
            state=CardDisplaySG.select_deck,
        ),
        state=CardDisplaySG.create_deck,
    ),
    Window(
        Format("Картка <b>{word}</b> дададзена да калодкі!"),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        Button(
            Const("← Назад да вынікаў"),
            id="back_results",
            on_click=on_done,
        ),
        state=CardDisplaySG.added,
        getter=added_getter,
    ),
)
