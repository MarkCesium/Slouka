from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import Card

from .base import BaseRepository


class CardRepository(BaseRepository[Card]):
    def __init__(self, session: AsyncSession):
        super().__init__(Card, session)
