from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.core.calendar import build_calendar_days
from src.core.plural import pluralize
from src.infra.tg.calendar import CalendarKeyboard
from src.infra.tg.strings import Buttons, Stats, Words
from src.services.stats import StatsService

from .common import get_dialog_data, get_user, on_back_to_menu
from .states import StatsSG

# ── Getters ──────────────────────────────────────────────────────────────────


@inject
async def overview_getter(
    dialog_manager: DialogManager,
    stats_service: FromDishka[StatsService],
    **kwargs: Any,
) -> dict[str, Any]:
    user = get_user(dialog_manager)
    if not user:
        return {"has_reviews": False, "calendar_weeks": []}

    tz = user.timezone
    now_local = datetime.now(ZoneInfo(tz))
    today_local = now_local.date()

    data = get_dialog_data(dialog_manager)
    year: int = data.get("cal_year", today_local.year)
    month: int = data.get("cal_month", today_local.month)

    active_days = await stats_service.get_calendar_data(user.id, year, month, tz)
    counts = await stats_service.get_review_counts(user.id, tz)

    calendar_weeks = build_calendar_days(
        year, month, active_days, today_local, has_streak=user.current_streak > 0
    )

    # Prev/next month labels
    prev_m = month - 1 if month > 1 else 12
    next_m = month + 1 if month < 12 else 1

    has_reviews = counts["week"] > 0 or counts["month"] > 0
    streak = user.current_streak
    longest = user.longest_streak
    streak_active_today = user.last_activity_date == today_local

    return {
        "calendar_weeks": calendar_weeks,
        "month_label": f"{Stats.MONTHS[month - 1]} {year}",
        "week": counts["week"],
        "week_cards": pluralize(counts["week"], *Words.REVIEW),
        "month_count": counts["month"],
        "month_cards": pluralize(counts["month"], *Words.REVIEW),
        "streak": streak,
        "streak_days": pluralize(streak, *Words.DAY),
        "longest": longest,
        "longest_days": pluralize(longest, *Words.DAY),
        "has_reviews": has_reviews,
        "has_streak": streak > 0,
        "streak_active_today": streak_active_today,
        "streak_at_risk": streak > 0 and not streak_active_today,
        "prev_month_label": Stats.MONTHS[prev_m - 1],
        "next_month_label": Stats.MONTHS[next_m - 1],
    }


@inject
async def decks_getter(
    dialog_manager: DialogManager,
    stats_service: FromDishka[StatsService],
    **kwargs: Any,
) -> dict[str, Any]:
    user = get_user(dialog_manager)
    if not user:
        return {"decks_text": "", "ease_text": "", "has_decks": False}

    deck_stats = await stats_service.get_deck_learned_stats(user.id)
    ease = await stats_service.get_ease_distribution(user.id)

    if not deck_stats:
        return {"decks_text": "", "ease_text": "", "has_decks": False}

    lines = [f"  {d['name']}: {d['learned']}/{d['total']} ({d['percent']}%)" for d in deck_stats]
    decks_text = "\n".join(lines)

    ease_text = (
        f"{Stats.EASE_EASY.format(easy=ease['easy'])}\n"
        f"{Stats.EASE_MEDIUM.format(medium=ease['medium'])}\n"
        f"{Stats.EASE_HARD.format(hard=ease['hard'])}"
    )

    return {
        "decks_text": decks_text,
        "ease_text": ease_text,
        "has_decks": True,
    }


# ── Callbacks ────────────────────────────────────────────────────────────────


async def on_prev_month(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    user = get_user(manager)
    if not user:
        return

    now_local = datetime.now(ZoneInfo(user.timezone))
    year: int = data.get("cal_year", now_local.year)
    month: int = data.get("cal_month", now_local.month)

    if month == 1:
        data["cal_year"] = year - 1
        data["cal_month"] = 12
    else:
        data["cal_month"] = month - 1


async def on_next_month(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    data = get_dialog_data(manager)
    user = get_user(manager)
    if not user:
        return

    now_local = datetime.now(ZoneInfo(user.timezone))
    year: int = data.get("cal_year", now_local.year)
    month: int = data.get("cal_month", now_local.month)

    if month == 12:
        data["cal_year"] = year + 1
        data["cal_month"] = 1
    else:
        data["cal_month"] = month + 1


# ── Predicates ───────────────────────────────────────────────────────────────


def no_reviews(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_reviews")


def no_deck_stats(data: dict[str, Any], *_: Any) -> bool:
    return not data.get("has_decks")


# ── Dialog ───────────────────────────────────────────────────────────────────

stats_dialog = Dialog(
    # ── Overview: calendar + counts ──────────────────────────────────
    Window(
        Const(Stats.TITLE),
        Format("<b>{month_label}</b>"),
        CalendarKeyboard(id="cal"),
        Row(
            Button(Const(Stats.PREV_MONTH), id="prev_m", on_click=on_prev_month),
            Button(Const(Stats.NEXT_MONTH), id="next_m", on_click=on_next_month),
        ),
        Format(Stats.STREAK_INFO, when="streak_active_today"),
        Format(Stats.STREAK_INFO_WARNING, when="streak_at_risk"),
        Format(Stats.WEEK_COUNT, when="has_reviews"),
        Format(Stats.MONTH_COUNT, when="has_reviews"),
        Const(Stats.NO_REVIEWS, when=no_reviews),
        SwitchTo(
            Const(Stats.DECK_STATS_BTN),
            id="to_decks",
            state=StatsSG.decks,
        ),
        Button(Const(Buttons.MENU), id="menu", on_click=on_back_to_menu),
        state=StatsSG.overview,
        getter=overview_getter,
    ),
    # ── Deck stats: learned % + ease distribution ────────────────────
    Window(
        Const(Stats.DECK_STATS_TITLE),
        Format("{decks_text}", when="has_decks"),
        Const(Stats.NO_DECKS, when=no_deck_stats),
        Const(Stats.EASE_TITLE, when="has_decks"),
        Format("{ease_text}", when="has_decks"),
        SwitchTo(
            Const(Buttons.BACK),
            id="back",
            state=StatsSG.overview,
        ),
        Button(Const(Buttons.MENU), id="menu", on_click=on_back_to_menu),
        state=StatsSG.decks,
        getter=decks_getter,
    ),
)
