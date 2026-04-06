from typing import Any

from aiogram.types import (
    CallbackQuery,
    ContentType,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from src.core.timezone import format_timezone, search_timezones, timezone_from_location
from src.services.user import UserService

from .common import get_dialog_data, get_user, on_back_to_menu
from .states import SettingsSG

HOURS: list[tuple[str, str]] = [(f"{h}:00", str(h)) for h in range(24)]
MINUTES: list[tuple[str, str]] = [(f":{m:02d}", str(m)) for m in range(0, 60, 10)]


# ── Getters ──────────────────────────────────────────────────────────────────


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
    tz_display = format_timezone(user.timezone)
    toggle_text = "Выключыць апавяшчэнні" if user.notifications_enabled else "Уключыць апавяшчэнні"

    return {
        "status": status,
        "hour": user.notification_hour,
        "minute": f"{user.notification_minute:02d}",
        "timezone": tz_display,
        "toggle_text": toggle_text,
        "hours": HOURS,
    }


async def select_minute_getter(
    dialog_manager: DialogManager,
    **kwargs: Any,
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    selected_hour = data.get("selected_hour", 0)
    return {
        "selected_hour": selected_hour,
        "minutes": MINUTES,
    }


async def tz_search_results_getter(
    dialog_manager: DialogManager,
    **kwargs: Any,
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    results: list[tuple[str, str]] = data.get("tz_results", [])
    return {"tz_results": results}


async def tz_confirm_getter(
    dialog_manager: DialogManager,
    **kwargs: Any,
) -> dict[str, Any]:
    data = get_dialog_data(dialog_manager)
    return {"selected_tz_label": data.get("selected_tz_label", "")}


# ── Callbacks ────────────────────────────────────────────────────────────────


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
    data = get_dialog_data(manager)
    data["selected_hour"] = int(item_id)
    await manager.switch_to(SettingsSG.select_minute)  # pyright: ignore[reportUnknownMemberType]


@inject
async def on_minute_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if not user:
        return
    data = get_dialog_data(manager)
    hour = data.get("selected_hour", 0)
    minute = int(item_id)
    await user_service.update_notification_time(user.id, hour, minute)
    await manager.switch_to(SettingsSG.main)  # pyright: ignore[reportUnknownMemberType]


# ── Timezone callbacks ───────────────────────────────────────────────────────


async def on_request_location(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    if not callback.message:
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Адправіць месцазнаходжанне", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await callback.message.answer(
        "Націсніце кнопку ніжэй, каб адправіць месцазнаходжанне:",
        reply_markup=kb,
    )


async def on_location_received(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
) -> None:
    if not message.location:
        return
    tz = timezone_from_location(message.location.latitude, message.location.longitude)
    if tz is None:
        await message.answer("Не ўдалося вызначыць часавы пояс. Паспрабуйце пошук па горадзе.")
        return
    data = get_dialog_data(manager)
    data["selected_tz"] = tz
    data["selected_tz_label"] = format_timezone(tz)
    await message.answer("📍 Месцазнаходжанне атрымана!", reply_markup=ReplyKeyboardRemove())
    await manager.switch_to(SettingsSG.tz_confirm)  # pyright: ignore[reportUnknownMemberType]


async def on_tz_search(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
) -> None:
    query = message.text or ""
    results = search_timezones(query)
    if not results:
        await message.answer("Нічога не знойдзена. Паспрабуйце яшчэ раз.")
        return
    data = get_dialog_data(manager)
    data["tz_results"] = results
    await manager.switch_to(SettingsSG.tz_search_results)  # pyright: ignore[reportUnknownMemberType]


async def on_tz_result_selected(
    callback: CallbackQuery,
    widget: Select[Any],
    manager: DialogManager,
    item_id: str,
) -> None:
    data = get_dialog_data(manager)
    data["selected_tz"] = item_id
    data["selected_tz_label"] = format_timezone(item_id)
    await manager.switch_to(SettingsSG.tz_confirm)  # pyright: ignore[reportUnknownMemberType]


@inject
async def on_tz_confirmed(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
    user_service: FromDishka[UserService],
) -> None:
    user = get_user(manager)
    if not user:
        return
    data = get_dialog_data(manager)
    tz = data.get("selected_tz", "")
    if tz:
        await user_service.update_timezone(user.id, tz)
    await manager.switch_to(SettingsSG.main)  # pyright: ignore[reportUnknownMemberType]


# ── Dialog ───────────────────────────────────────────────────────────────────


settings_dialog = Dialog(
    # Main settings
    Window(
        Format(
            "<b>⚙️ Налады</b>\n\n"
            "Апавяшчэнні: {status}\n"
            "Час: {hour}:{minute}\n"
            "Часавы пояс: {timezone}"
        ),
        Button(Format("{toggle_text}"), id="toggle", on_click=on_toggle),
        SwitchTo(Const("🕐 Змяніць час"), id="change_hour", state=SettingsSG.select_hour),
        SwitchTo(Const("🌍 Змяніць часавы пояс"), id="change_tz", state=SettingsSG.select_timezone),
        Button(Const("← Меню"), id="menu", on_click=on_back_to_menu),
        state=SettingsSG.main,
        getter=settings_getter,
    ),
    # Select hour
    Window(
        Const("<b>Абярыце гадзіну апавяшчэння:</b>"),
        Group(
            Select(
                Format("{item[0]}"),
                id="hour_select",
                item_id_getter=lambda item: item[1],
                items="hours",
                on_click=on_hour_selected,  # pyright: ignore[reportArgumentType]
            ),
            width=6,
        ),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.main),
        state=SettingsSG.select_hour,
        getter=settings_getter,
    ),
    # Select minute
    Window(
        Format("<b>Абярыце хвіліны ({selected_hour}:??):</b>"),
        Group(
            Select(
                Format("{item[0]}"),
                id="minute_select",
                item_id_getter=lambda item: item[1],
                items="minutes",
                on_click=on_minute_selected,  # pyright: ignore[reportArgumentType]
            ),
            width=3,
        ),
        SwitchTo(Const("← Назад"), id="back_hour", state=SettingsSG.select_hour),
        state=SettingsSG.select_minute,
        getter=select_minute_getter,
    ),
    # Timezone: choose method
    Window(
        Const("<b>Як вызначыць часавы пояс?</b>"),
        Button(
            Const("📍 Адправіць месцазнаходжанне"),
            id="request_loc",
            on_click=on_request_location,
        ),
        MessageInput(on_location_received, content_types=[ContentType.LOCATION]),
        SwitchTo(Const("🔍 Пошук па горадзе"), id="tz_search", state=SettingsSG.tz_search_input),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.main),
        state=SettingsSG.select_timezone,
    ),
    # Timezone: search input
    Window(
        Const("<b>Увядзіце назву горада</b> (напрыклад, Minsk, Warsaw, Tokyo):"),
        MessageInput(on_tz_search, content_types=[ContentType.TEXT]),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.select_timezone),
        state=SettingsSG.tz_search_input,
    ),
    # Timezone: search results
    Window(
        Const("<b>Абярыце часавы пояс:</b>"),
        Select(
            Format("{item[0]}"),
            id="tz_result_select",
            item_id_getter=lambda item: item[1],
            items="tz_results",
            on_click=on_tz_result_selected,  # pyright: ignore[reportArgumentType]
        ),
        SwitchTo(Const("🔍 Шукаць яшчэ"), id="search_again", state=SettingsSG.tz_search_input),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.select_timezone),
        state=SettingsSG.tz_search_results,
        getter=tz_search_results_getter,
    ),
    # Timezone: confirm
    Window(
        Format("<b>Ваш часавы пояс:</b> {selected_tz_label}\n\nПацвердзіць?"),
        Button(Const("✅ Пацвердзіць"), id="tz_confirm", on_click=on_tz_confirmed),
        SwitchTo(Const("← Назад"), id="back", state=SettingsSG.select_timezone),
        state=SettingsSG.tz_confirm,
        getter=tz_confirm_getter,
    ),
)
