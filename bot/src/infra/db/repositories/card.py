from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import Card

from .base import BaseRepository


class CardRepository(BaseRepository[Card]):
    def __init__(self, session: AsyncSession):
        super().__init__(Card, session)

    async def get_due_cards(self, deck_id: int, limit: int = 20) -> Sequence[Card]:
        now = datetime.now(UTC)
        return await self.find(
            filters=[
                Card.deck_id == deck_id,
                or_(Card.next_review_date <= now, Card.is_new == True),  # noqa: E712
            ],
            order_by=Card.next_review_date.asc(),
            limit=limit,
        )
