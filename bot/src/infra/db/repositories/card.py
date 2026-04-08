from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, Row, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import Card
from src.infra.db.models.deck import Deck

from .base import BaseRepository


def due_cards_filter(now: datetime) -> ColumnElement[bool]:
    """Reusable filter: cards that are due for review (overdue OR new)."""
    return or_(Card.next_review_date <= now, Card.is_new == True)  # noqa: E712


class CardRepository(BaseRepository[Card]):
    def __init__(self, session: AsyncSession):
        super().__init__(Card, session)

    async def get_due_cards(self, deck_id: int, limit: int = 20) -> Sequence[Card]:
        now = datetime.now(UTC)
        return await self.find(
            filters=[
                Card.deck_id == deck_id,
                due_cards_filter(now),
            ],
            order_by=Card.next_review_date.asc(),
            limit=limit,
        )

    async def get_ease_distribution(self, user_id: int) -> dict[str, int]:
        """Bucket non-new cards by ease factor: hard/medium/easy."""
        query = (
            select(
                func.count(case((Card.ease_factor < 2.0, Card.id))).label("hard"),
                func.count(
                    case(
                        (
                            (Card.ease_factor >= 2.0) & (Card.ease_factor < 2.5),
                            Card.id,
                        )
                    )
                ).label("medium"),
                func.count(case((Card.ease_factor >= 2.5, Card.id))).label("easy"),
            )
            .select_from(Card)
            .join(Deck, Card.deck_id == Deck.id)
            .where(Deck.user_id == user_id, Card.is_new == False)  # noqa: E712
        )
        result = await self.session.execute(query)
        row = result.one()
        return {"hard": row.hard, "medium": row.medium, "easy": row.easy}

    async def get_learned_stats_per_deck(self, user_id: int) -> Sequence[Row[tuple[str, int, int]]]:
        """Return (deck_name, learned_count, total_count) per deck."""
        learned_filter = (Card.is_new == False) & (Card.repetitions >= 1)  # noqa: E712
        query = (
            select(
                Deck.name.label("deck_name"),
                func.count(case((learned_filter, Card.id))).label("learned"),
                func.count(Card.id).label("total"),
            )
            .select_from(Deck)
            .outerjoin(Card, Card.deck_id == Deck.id)
            .where(Deck.user_id == user_id)
            .group_by(Deck.id, Deck.name)
        )
        result = await self.session.execute(query)
        return result.all()
