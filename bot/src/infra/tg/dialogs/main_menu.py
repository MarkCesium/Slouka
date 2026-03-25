from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from .states import DeckManagementSG, LookupSG, MainMenuSG, ReviewSG


async def on_search(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(LookupSG.enter_word)


async def on_decks(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(DeckManagementSG.list_decks)


async def on_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(ReviewSG.select_deck)


main_menu_dialog = Dialog(
    Window(
        Const("<b>Main Menu</b>\n\nWhat would you like to do?"),
        Button(Const("🔍 Search Word"), id="search", on_click=on_search),
        Button(Const("📚 My Decks"), id="decks", on_click=on_decks),
        Button(Const("🧠 Review"), id="review", on_click=on_review),
        state=MainMenuSG.menu,
    ),
)
