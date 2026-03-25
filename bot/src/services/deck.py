from collections.abc import Sequence
from datetime import UTC, datetime

from src.infra.db.models import Card, Deck
from src.infra.db.uow import UnitOfWork


class DeckService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_user_decks(self, user_id: int) -> Sequence[Deck]:
        async with self._uow:
            return await self._uow.decks.get_all(user_id=user_id)

    async def create_deck(self, user_id: int, name: str) -> Deck:
        async with self._uow:
            return await self._uow.decks.create(user_id=user_id, name=name)

    async def get_deck_stats(self, deck_id: int) -> dict[str, int]:
        async with self._uow:
            total = await self._uow.cards.count(filters=[Card.deck_id == deck_id])
            new = await self._uow.cards.count(
                filters=[Card.deck_id == deck_id, Card.is_new == True]  # noqa: E712
            )
            now = datetime.now(UTC)
            due = await self._uow.cards.count(
                filters=[
                    Card.deck_id == deck_id,
                    Card.is_new == False,  # noqa: E712
                    Card.next_review_date <= now,
                ]
            )
            return {"total": total, "new": new, "due": due}
