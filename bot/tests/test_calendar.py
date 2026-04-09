from datetime import date

from src.core.calendar import (
    MARKER_EMPTY,
    MARKER_FIRE,
    MARKER_INACTIVE,
    MARKER_WARNING,
    build_calendar_days,
)


def test_active_days_marked_with_fire() -> None:
    # April 2026: starts on Wednesday
    weeks = build_calendar_days(
        2026, 4, active_days={8, 15}, user_today=date(2026, 4, 20), has_streak=True
    )
    # Flatten to find day 8 and 15
    all_days = [d for week in weeks for d in week]
    day_8 = next(d for d in all_days if d.day == 8)
    day_15 = next(d for d in all_days if d.day == 15)
    assert day_8.marker == MARKER_FIRE
    assert day_15.marker == MARKER_FIRE


def test_today_without_activity_and_streak_shows_warning() -> None:
    weeks = build_calendar_days(
        2026, 4, active_days=set(), user_today=date(2026, 4, 10), has_streak=True
    )
    all_days = [d for week in weeks for d in week]
    day_10 = next(d for d in all_days if d.day == 10)
    assert day_10.marker == MARKER_WARNING


def test_today_without_activity_no_streak_shows_inactive() -> None:
    weeks = build_calendar_days(
        2026, 4, active_days=set(), user_today=date(2026, 4, 10), has_streak=False
    )
    all_days = [d for week in weeks for d in week]
    day_10 = next(d for d in all_days if d.day == 10)
    assert day_10.marker == MARKER_INACTIVE


def test_future_days_show_empty() -> None:
    weeks = build_calendar_days(
        2026, 4, active_days=set(), user_today=date(2026, 4, 15), has_streak=False
    )
    all_days = [d for week in weeks for d in week if not d.is_padding]
    day_20 = next(d for d in all_days if d.day == 20)
    assert day_20.marker == MARKER_EMPTY


def test_padding_cells_are_empty() -> None:
    # April 2026 starts on Wednesday, so Mon/Tue of first week are padding
    weeks = build_calendar_days(
        2026, 4, active_days=set(), user_today=date(2026, 4, 15), has_streak=False
    )
    first_week = weeks[0]
    assert first_week[0].is_padding  # Monday
    assert first_week[0].marker == MARKER_EMPTY
    assert first_week[1].is_padding  # Tuesday


def test_past_inactive_days() -> None:
    weeks = build_calendar_days(
        2026, 4, active_days={5}, user_today=date(2026, 4, 15), has_streak=True
    )
    all_days = [d for week in weeks for d in week if not d.is_padding]
    day_3 = next(d for d in all_days if d.day == 3)
    assert day_3.marker == MARKER_INACTIVE


def test_today_active_shows_fire_not_warning() -> None:
    """If today is in active_days, show fire even with streak."""
    weeks = build_calendar_days(
        2026, 4, active_days={10}, user_today=date(2026, 4, 10), has_streak=True
    )
    all_days = [d for week in weeks for d in week if not d.is_padding]
    day_10 = next(d for d in all_days if d.day == 10)
    assert day_10.marker == MARKER_FIRE


def test_seven_columns_per_week() -> None:
    weeks = build_calendar_days(
        2026, 4, active_days=set(), user_today=date(2026, 4, 1), has_streak=False
    )
    for week in weeks:
        assert len(week) == 7
