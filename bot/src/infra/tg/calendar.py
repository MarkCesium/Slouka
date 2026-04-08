from aiogram.types import CallbackQuery, InlineKeyboardButton, KeyboardButton
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import RawKeyboard
from aiogram_dialog.api.protocols import DialogProtocol
from aiogram_dialog.widgets.kbd.base import Keyboard

from src.core.calendar import CalendarDay
from src.infra.tg.strings import Stats

NOOP_CALLBACK = "cal_noop"


class CalendarKeyboard(Keyboard):
    """Custom aiogram-dialog widget that renders an inline keyboard calendar grid."""

    async def _render_keyboard(
        self,
        data: dict[str, object],
        manager: DialogManager,
    ) -> RawKeyboard:
        calendar_weeks: list[list[CalendarDay]] | None = data.get("calendar_weeks")  # type: ignore[assignment]
        if not calendar_weeks:
            return []

        rows: list[list[InlineKeyboardButton | KeyboardButton]] = []

        # Weekday header row
        header: list[InlineKeyboardButton | KeyboardButton] = [
            InlineKeyboardButton(text=wd, callback_data=NOOP_CALLBACK) for wd in Stats.WEEKDAYS
        ]
        rows.append(header)

        # Day rows
        for week in calendar_weeks:
            row: list[InlineKeyboardButton | KeyboardButton] = [
                InlineKeyboardButton(text=day.marker, callback_data=NOOP_CALLBACK) for day in week
            ]
            rows.append(row)

        return rows

    async def _process_own_callback(
        self,
        callback: CallbackQuery,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        await callback.answer()
        return True

    async def _process_item_callback(
        self,
        callback: CallbackQuery,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        await callback.answer()
        return True
