from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import User
from src.infra.db.models.card import Card
from src.infra.db.models.deck import Deck

from .base import BaseRepository
from .card import due_cards_filter


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_users_to_notify(self) -> Sequence[User]:
        now = datetime.now(UTC)
        due_card_exists = (
            select(Card.id)
            .join(Deck, Card.deck_id == Deck.id)
            .where(
                Deck.user_id == User.id,
                due_cards_filter(now),
            )
            .correlate(User)
            .exists()
        )
        return await self.find(
            filters=[
                User.notifications_enabled == True,  # noqa: E712
                User.onboarding_completed == True,  # noqa: E712
                due_card_exists,
            ]
        )
