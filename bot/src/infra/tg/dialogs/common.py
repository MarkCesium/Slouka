from typing import Any, cast

from aiogram_dialog import DialogManager

from src.infra.db.models import User


def get_dialog_data(manager: DialogManager) -> dict[str, Any]:
    return cast(dict[str, Any], manager.dialog_data)


def get_start_data(manager: DialogManager) -> dict[str, Any]:
    data = manager.start_data
    if isinstance(data, dict):
        return cast(dict[str, Any], data)
    return {}


def get_user(manager: DialogManager) -> User | None:
    data: dict[str, Any] = cast(dict[str, Any], manager.middleware_data)
    user = data.get("user")
    if isinstance(user, User):
        return user
    return None
