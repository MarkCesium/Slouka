from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from .states import DeckManagementSG, LookupSG, MainMenuSG, ReviewSG, SettingsSG


async def on_search(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(LookupSG.enter_word)  # pyright: ignore[reportUnknownMemberType]


async def on_decks(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(DeckManagementSG.list_decks)  # pyright: ignore[reportUnknownMemberType]


async def on_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(ReviewSG.select_deck)  # pyright: ignore[reportUnknownMemberType]


async def on_settings(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(SettingsSG.main)  # pyright: ignore[reportUnknownMemberType]


main_menu_dialog = Dialog(
    Window(
        Const("<b>Галоўнае меню</b>\n\nШто б вы хацелі зрабіць?"),
        Button(Const("🔍 Пошук слова"), id="search", on_click=on_search),
        Button(Const("📚 Мае калодкі"), id="decks", on_click=on_decks),
        Button(Const("🧠 Практыка"), id="review", on_click=on_review),
        Button(Const("⚙️ Налады"), id="settings", on_click=on_settings),
        state=MainMenuSG.menu,
    ),
)
