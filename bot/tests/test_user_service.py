import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.uow import UnitOfWork
from src.services.user import UserService

from .conftest import create_user


class TestGetOrCreateUser:
    async def test_new_user(self, uow: UnitOfWork) -> None:
        service = UserService(uow)
        user, is_new = await service.get_or_create_user(12345, "Test User")
        assert is_new is True
        assert user.id == 12345
        assert user.name == "Test User"

    async def test_existing_user(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=12345, name="Original")
        await session.commit()

        service = UserService(uow)
        user, is_new = await service.get_or_create_user(12345, "New Name")
        assert is_new is False
        assert user.id == 12345


class TestToggleNotifications:
    async def test_toggle(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1, notifications_enabled=True)
        await session.commit()

        service = UserService(uow)
        new_state = await service.toggle_notifications(1)
        assert new_state is False

        new_state = await service.toggle_notifications(1)
        assert new_state is True


class TestUpdateTimezone:
    async def test_valid_timezone(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        await service.update_timezone(1, "Europe/Minsk")

    async def test_invalid_timezone(self, session: AsyncSession, uow: UnitOfWork) -> None:
        await create_user(session, id=1)
        await session.commit()

        service = UserService(uow)
        with pytest.raises(ValueError, match="Invalid timezone"):
            await service.update_timezone(1, "Invalid/Timezone")
