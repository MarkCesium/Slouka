from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import Deck

from .base import BaseRepository


class DeckRepository(BaseRepository[Deck]):
    def __init__(self, session: AsyncSession):
        super().__init__(Deck, session)