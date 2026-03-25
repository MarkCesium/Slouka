import logging
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Row
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.infra.schemas.verbum import ParsedCard
from src.infra.verbum.parser import format_card_for_telegram
from src.services.verbum import VerbumService

from .common import get_dialog_data
from .states import CardDisplaySG, LookupSG, MainMenuSG

logger = logging.getLogger(__name__)


@inject
async def on_word_entered(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
    verbum_service: FromDishka[VerbumService],
) -> None:
    word = message.text
    if not word or not word.strip():
        await message.answer("Калі ласка, увядзіце слова.")
        return

    word = word.strip()
    cards = await verbum_service.search_word(word)

    if not cards:
        await message.answer(f"Не знойдзена вынікаў для <b>{word}</b>. Паспрабуйце іншае слова.")
        return

    data = get_dialog_data(manager)
    data["cards"] = [c.model_dump() for c in cards]
    data["current_index"] = 0
    data["query"] = word

    await manager.switch_to(LookupSG.results)


async def results_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    cards_data: list[dict[str, Any]] = data.get("cards", [])
    index: int = data.get("current_index", 0)
    query: str = data.get("query", "")

    if not cards_data:
        return {
            "card_text": "Не знойдзена вынікаў.",
            "nav_info": "",
            "query": query,
        }

    card = ParsedCard.model_validate(cards_data[index])
    card_text = format_card_for_telegram(card)
    total = len(cards_data)
    nav_info = f"Вынік {index + 1} з {total}" if total > 1 else ""

    return {
        "card_text": card_text,
        "nav_info": nav_info,
        "query": query,
        "has_prev": index > 0,
        "has_next": index < total - 1,
    }


async def on_prev(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    index: int = data.get("current_index", 0)
    if index > 0:
        data["current_index"] = index - 1


async def on_next(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    cards: list[Any] = data.get("cards", [])
    index: int = data.get("current_index", 0)
    if index < len(cards) - 1:
        data["current_index"] = index + 1


async def on_add_to_deck(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    cards_data: list[dict[str, Any]] = data.get("cards", [])
    index: int = data.get("current_index", 0)

    if cards_data:
        await manager.start(
            CardDisplaySG.select_deck,
            data={"parsed_card": cards_data[index]},
        )


async def on_new_search(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    get_dialog_data(manager).clear()
    await manager.switch_to(LookupSG.enter_word)


async def on_back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(MainMenuSG.menu, mode=StartMode.RESET_STACK)


lookup_dialog = Dialog(
    Window(
        Const("<b>Пошук слова</b>\n\nУвядзіце беларускае слова для пошуку:"),
        MessageInput(on_word_entered),
        Button(Const("← Назад"), id="back", on_click=on_back_to_menu),
        state=LookupSG.enter_word,
    ),
    Window(
        Format("{card_text}"),
        Format("\n{nav_info}", when="nav_info"),
        Group(
            Row(
                Button(
                    Const("← Папярэдні"),
                    id="prev",
                    on_click=on_prev,
                    when="has_prev",
                ),
                Button(
                    Const("Наступны →"),
                    id="next",
                    on_click=on_next,
                    when="has_next",
                ),
            ),
            Button(
                Const("📥 Дадаць да калодкі"),
                id="add",
                on_click=on_add_to_deck,
            ),
            Button(
                Const("🔍 Новы пошук"),
                id="new_search",
                on_click=on_new_search,
            ),
            Button(
                Const("← Меню"),
                id="menu",
                on_click=on_back_to_menu,
            ),
        ),
        state=LookupSG.results,
        getter=results_getter,
        parse_mode="HTML",
    ),
)
