from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Group, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.services.user import UserService

from .common import get_user, on_back_to_menu
from .states import SettingsSG

TIMEZONES: list[tuple[str, str]] = [
    ("Мінск (UTC+3)", "Europe/Minsk"),
    ("Кіеў (UTC+2/+3)", "Europe/Kyiv"),
    ("Варшава (UTC+1/+2)", "Europe/Warsaw"),
    ("Вільнюс (UTC+2/+3)", "Europe/Vilnius"),
]

HOURS: list[tuple[str, str]] = [
    ("8:00", "8"),
    ("9:00", "9"),
    ("10:00", "10"),
    ("12:00", "12"),
    ("14:00", "14"),
    ("18:00", "18"),
    ("20:00", "20"),
    ("21:00", "21"),
]

TIMEZONE_DISPLAY: dict[str, str] = {tz: label for label, tz in TIMEZONES}


@inject
async def settings_getter(
    dialog_manager: DialogManager,
    user_service: FromDishka[UserService],
    **kwargs: Any,
) -> dict[str, Any]:
    user = get_user(dialog_manager)
    if not user:
        return {}

    status = "✅ Уключаны" if user.notifications_enabled else "❌ Выключаны"
    tz_display = TIMEZONE_DISPLAY.get(user.timezone, user.timezone)
    toggle_text = "Выключыць апавяшчэнні" if user.notifications_enabled else "Уключыць апавяшчэнні"

    return {
        "status": status,
        "hour": f"{user.notification_hour}:00",
        "timezone": tz_display,
        "toggle_text": toggle_text,
        "timezones": TIMEZONES,
        "hours": HOURS,
    }


@inject
async def on_toggle(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if not user:
        return
    await user_service.toggle_notifications(user.id)


@inject
async def on_hour_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if not user:
        return
    await user_service.update_notification_hour(user.id, int(item_id))
    await manager.switch_to(SettingsSG.main)  # pyright: ignore[reportUnknownMemberType]


@inject
async def on_timezone_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if not user:
        return
    await user_service.update_timezone(user.id, item_id)
    await manager.switch_to(SettingsSG.main)  # pyright: ignore[reportUnknownMemberType]


settings_dialog = Dialog(
    Window(
        Format("<b>⚙️ Налады</b>\n\nАпавяшчэнні: {status}\nЧас: {hour}\nЧасавы пояс: {timezone}"),
        Button(Format("{toggle_text}"), id="toggle", on_click=on_toggle),
        SwitchTo(Const("🕐 Змяніць час"), id="change_hour", state=SettingsSG.select_hour),
        SwitchTo(Const("🌍 Змяніць часавы пояс"), id="change_tz", state=SettingsSG.select_timezone),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        state=SettingsSG.main,
        getter=settings_getter,
    ),
    Window(
        Const("<b>Абярыце час апавяшчэння:</b>"),
        Group(
            Select(
                Format("{item[0]}"),
                id="hour_select",
                item_id_getter=lambda item: item[1],
                items="hours",
                on_click=on_hour_selected,  # pyright: ignore[reportArgumentType]
            ),
            width=4,
        ),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.main),
        state=SettingsSG.select_hour,
        getter=settings_getter,
    ),
    Window(
        Const("<b>Абярыце часавы пояс:</b>"),
        Select(
            Format("{item[0]}"),
            id="tz_select",
            item_id_getter=lambda item: item[1],
            items="timezones",
            on_click=on_timezone_selected,  # pyright: ignore[reportArgumentType]
        ),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.main),
        state=SettingsSG.select_timezone,
        getter=settings_getter,
    ),
)
