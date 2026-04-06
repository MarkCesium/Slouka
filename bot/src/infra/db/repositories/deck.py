from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Row, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import Card, Deck

from .base import BaseRepository


class DeckRepository(BaseRepository[Deck]):
    def __init__(self, session: AsyncSession):
        super().__init__(Deck, session)

    async def get_decks_with_stats(self, user_id: int) -> Sequence[Row[tuple[Deck, int, int, int]]]:
        """Return all user decks with card stats (total, new, due) in one query."""
        now = datetime.now(UTC)
        query = (
            select(
                Deck,
                func.count(Card.id).label("total"),
                func.count(case((Card.is_new == True, Card.id))).label("new"),  # noqa: E712
                func.count(
                    case(
                        (
                            (Card.is_new == False) & (Card.next_review_date <= now),  # noqa: E712
                            Card.id,
                        )
                    )
                ).label("due"),
            )
            .outerjoin(Card, Card.deck_id == Deck.id)
            .where(Deck.user_id == user_id)
            .group_by(Deck.id)
        )
        result = await self.session.execute(query)
        return result.all()

    async def get_single_deck_stats(self, deck_id: int) -> Row[tuple[int, int, int]]:
        """Return (total, new, due) for a single deck in one query."""
        now = datetime.now(UTC)
        query = (
            select(
                func.count(Card.id).label("total"),
                func.count(case((Card.is_new == True, Card.id))).label("new"),  # noqa: E712
                func.count(
                    case(
                        (
                            (Card.is_new == False) & (Card.next_review_date <= now),  # noqa: E712
                            Card.id,
                        )
                    )
                ).label("due"),
            )
            .select_from(Card)
            .where(Card.deck_id == deck_id)
        )
        result = await self.session.execute(query)
        return result.one()
