import calendar as cal_module
from dataclasses import dataclass
from datetime import date

MARKER_FIRE = "🔥"
MARKER_WARNING = "🔶"
MARKER_INACTIVE = "▫️"
MARKER_EMPTY = "·"


@dataclass
class CalendarDay:
    day: int
    marker: str
    is_padding: bool


def build_calendar_days(
    year: int,
    month: int,
    active_days: set[int],
    user_today: date,
    has_streak: bool,
) -> list[list[CalendarDay]]:
    """Build a grid of calendar days with activity markers."""
    calendar = cal_module.Calendar(firstweekday=0)
    target_date = date(year, month, 1)
    is_current_month = user_today.year == target_date.year and user_today.month == target_date.month

    weeks: list[list[CalendarDay]] = []
    for week in calendar.monthdayscalendar(year, month):
        row: list[CalendarDay] = []
        for day_num in week:
            if day_num == 0:
                row.append(CalendarDay(day=0, marker=MARKER_EMPTY, is_padding=True))
                continue

            if day_num in active_days:
                marker = MARKER_FIRE
            elif is_current_month and day_num == user_today.day:
                marker = MARKER_WARNING if has_streak else MARKER_INACTIVE
            elif is_current_month and day_num > user_today.day:
                marker = MARKER_EMPTY
            else:
                marker = MARKER_INACTIVE

            row.append(CalendarDay(day=day_num, marker=marker, is_padding=False))
        weeks.append(row)
    return weeks
