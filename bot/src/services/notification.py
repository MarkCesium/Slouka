from collections.abc import Sequence

from src.infra.db.models import User
from src.infra.db.uow import UnitOfWork


class NotificationService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_users_to_notify(self) -> Sequence[User]:
        async with self._uow:
            return await self._uow.users.get_users_to_notify()

    async def disable_notifications(self, user_id: int) -> None:
        async with self._uow:
            await self._uow.users.update(user_id, notifications_enabled=False)
