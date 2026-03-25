from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
