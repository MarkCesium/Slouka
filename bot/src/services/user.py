from datetime import date, timedelta
from zoneinfo import available_timezones

from src.core.exceptions import EntityNotFoundError
from src.infra.db.models import User
from src.infra.db.uow import UnitOfWork

_VALID_TIMEZONES: set[str] = available_timezones()


class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_or_create_user(self, tg_user_id: int, name: str) -> tuple[User, bool]:
        async with self._uow:
            user = await self._uow.users.get_by_id(tg_user_id)
            if user is not None:
                return user, False

            user = await self._uow.users.create(id=tg_user_id, name=name)
            return user, True

    async def complete_onboarding(self, user_id: int) -> None:
        async with self._uow:
            await self._uow.users.update(user_id, onboarding_completed=True)

    async def toggle_notifications(self, user_id: int) -> bool:
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            if user is None:
                raise EntityNotFoundError(f"User {user_id} not found")
            new_state = not user.notifications_enabled
            await self._uow.users.update(user_id, notifications_enabled=new_state)
            return new_state

    async def update_notification_time(self, user_id: int, hour: int, minute: int) -> None:
        async with self._uow:
            await self._uow.users.update(
                user_id, notification_hour=hour, notification_minute=minute
            )

    async def update_timezone(self, user_id: int, timezone: str) -> None:
        if timezone not in _VALID_TIMEZONES:
            raise ValueError(f"Invalid timezone: {timezone}")
        async with self._uow:
            await self._uow.users.update(user_id, timezone=timezone)

    async def update_streak(self, user_id: int, today: date) -> int:
        async with self._uow:
            user = await self._uow.users.get_by_id(user_id)
            if user is None:
                raise EntityNotFoundError(f"User {user_id} not found")

            if user.last_activity_date == today:
                return user.current_streak

            if user.last_activity_date == today - timedelta(days=1):
                new_streak = user.current_streak + 1
            else:
                new_streak = 1

            longest = max(user.longest_streak, new_streak)
            await self._uow.users.update(
                user_id,
                current_streak=new_streak,
                longest_streak=longest,
                last_activity_date=today,
            )
            return new_streak
