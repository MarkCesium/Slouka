from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from src.core.plural import pluralize
from src.infra.tg.strings import MainMenu, Words

from .common import get_user
from .states import DeckManagementSG, LookupSG, MainMenuSG, ReviewSG, SettingsSG, StatsSG


async def main_menu_getter(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    user = get_user(dialog_manager)
    streak = user.current_streak if user else 0
    active_today = False
    if user and streak > 0:
        today_local = datetime.now(ZoneInfo(user.timezone)).date()
        active_today = user.last_activity_date == today_local
    return {
        "streak": streak,
        "streak_days": pluralize(streak, *Words.DAY),
        "streak_active_today": active_today,
    }


def streak_active_today(data: dict[str, Any], *_: Any) -> bool:
    return bool(data.get("streak_active_today"))


def streak_at_risk(data: dict[str, Any], *_: Any) -> bool:
    return bool(data.get("streak")) and not data.get("streak_active_today")


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
        Format(MainMenu.STREAK, when=streak_active_today),
        Format(MainMenu.STREAK_WARNING, when=streak_at_risk),
        Button(Const(MainMenu.SEARCH), id="search", on_click=on_search),
        Button(Const(MainMenu.DECKS), id="decks", on_click=on_decks),
        Button(Const(MainMenu.PRACTICE), id="review", on_click=on_review),
        Button(Const(MainMenu.STATS), id="stats", on_click=on_stats),
        Button(Const(MainMenu.SETTINGS), id="settings", on_click=on_settings),
        state=MainMenuSG.menu,
        getter=main_menu_getter,
    ),
)
