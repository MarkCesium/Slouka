from src.infra.db.models import User
from src.infra.db.uow import UnitOfWork


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
