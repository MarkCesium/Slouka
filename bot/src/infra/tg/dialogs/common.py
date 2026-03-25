from typing import Any

from aiogram_dialog import DialogManager

from src.infra.db.models import User

_ManagerAny = Any


def get_dialog_data(manager: DialogManager) -> dict[str, Any]:
    m: _ManagerAny = manager
    result: dict[str, Any] = m.dialog_data
    return result


def get_start_data(manager: DialogManager) -> dict[str, Any]:
    m: _ManagerAny = manager
    data: Any = m.start_data
    if isinstance(data, dict):
        result: dict[str, Any] = data # pyright: ignore[reportUnknownVariableType]
        return result
    return {}


def get_user(manager: DialogManager) -> User | None:
    m: _ManagerAny = manager
    data: dict[str, Any] = m.middleware_data
    user = data.get("user")
    if isinstance(user, User):
        return user
    return None
