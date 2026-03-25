import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from dishka import AsyncContainer

from src.services.user import UserService

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        tg_user = None
        if event.message and event.message.from_user:
            tg_user = event.message.from_user
        elif event.callback_query and event.callback_query.from_user:
            tg_user = event.callback_query.from_user

        if tg_user is None:
            return await handler(event, data)

        container: AsyncContainer = data["dishka_container"]
        async with container() as request_container:
            user_service = await request_container.get(UserService)
            user, is_new = await user_service.get_or_create_user(tg_user.id, tg_user.full_name)
            data["user"] = user
            data["is_new_user"] = is_new

        return await handler(event, data)
