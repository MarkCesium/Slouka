from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.uow import UnitOfWork
from src.services.user import UserService

from .conftest import create_user


class TestUpdateStreak:
    async def test_first_activity_sets_streak_to_1(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        streak = await service.update_streak(1, date(2026, 4, 8))
        assert streak == 1

    async def test_same_day_no_change(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        await service.update_streak(1, date(2026, 4, 8))
        streak = await service.update_streak(1, date(2026, 4, 8))
        assert streak == 1

    async def test_consecutive_day_increments(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        await service.update_streak(1, date(2026, 4, 8))
        await service.update_streak(1, date(2026, 4, 9))
        streak = await service.update_streak(1, date(2026, 4, 10))
        assert streak == 3

    async def test_gap_resets_to_1(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        await service.update_streak(1, date(2026, 4, 8))
        await service.update_streak(1, date(2026, 4, 9))
        streak = await service.update_streak(1, date(2026, 4, 11))  # skipped Apr 10
        assert streak == 1

    async def test_longest_streak_tracked(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        today = date(2026, 4, 1)
        for i in range(5):
            await service.update_streak(1, today + timedelta(days=i))

        # Break streak
        await service.update_streak(1, today + timedelta(days=10))

        # Verify longest is preserved
        async with uow:
            user = await uow.users.get_by_id(1)
            assert user is not None
            assert user.longest_streak == 5
            assert user.current_streak == 1

    async def test_user_not_found_raises(self, uow: UnitOfWork) -> None:
        service = UserService(uow)
        with pytest.raises(Exception, match="not found"):
            await service.update_streak(999, date(2026, 4, 8))
