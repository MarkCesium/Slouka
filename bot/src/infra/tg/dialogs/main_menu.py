from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from src.core.plural import pluralize
from src.infra.tg.strings import MainMenu, Words

from .common import get_user, has_streak
from .states import DeckManagementSG, LookupSG, MainMenuSG, ReviewSG, SettingsSG, StatsSG


async def main_menu_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    user = get_user(dialog_manager)
    streak = user.current_streak if user else 0
    return {"streak": streak, "streak_days": pluralize(streak, *Words.DAY)}


async def on_search(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(LookupSG.enter_word)  # pyright: ignore[reportUnknownMemberType]


async def on_decks(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(DeckManagementSG.list_decks)  # pyright: ignore[reportUnknownMemberType]


async def on_review(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(ReviewSG.select_deck)  # pyright: ignore[reportUnknownMemberType]


async def on_stats(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(StatsSG.overview)  # pyright: ignore[reportUnknownMemberType]


async def on_settings(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    await manager.start(SettingsSG.main)  # pyright: ignore[reportUnknownMemberType]


main_menu_dialog = Dialog(
    Window(
        Const(MainMenu.TITLE),
        Format(MainMenu.STREAK, when=has_streak),
        Button(Const(MainMenu.SEARCH), id="search", on_click=on_search),
        Button(Const(MainMenu.DECKS), id="decks", on_click=on_decks),
        Button(Const(MainMenu.PRACTICE), id="review", on_click=on_review),
        Button(Const(MainMenu.STATS), id="stats", on_click=on_stats),
        Button(Const(MainMenu.SETTINGS), id="settings", on_click=on_settings),
        state=MainMenuSG.menu,
        getter=main_menu_getter,
    ),
)
