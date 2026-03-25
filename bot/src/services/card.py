from collections.abc import Sequence
from datetime import UTC, datetime

from src.infra.db.models import Card
from src.infra.db.uow import UnitOfWork
from src.infra.schemas.verbum import ParsedCard
from src.services.sm2 import SM2Service


class CardService:
    def __init__(self, uow: UnitOfWork, sm2: SM2Service) -> None:
        self._uow = uow
        self._sm2 = sm2

    async def create_card(self, deck_id: int, parsed_card: ParsedCard) -> Card | None:
        async with self._uow:
            existing = await self._uow.cards.find(
                filters=[Card.deck_id == deck_id, Card.word == parsed_card.headword],
                limit=1,
            )
            if existing:
                return None

            definition_parts = []
            for d in parsed_card.definitions:
                prefix = f"{d.number}. " if d.number else ""
                definition_parts.append(f"{prefix}{d.text}")

            examples_parts = []
            for d in parsed_card.definitions:
                examples_parts.extend(d.examples)

            return await self._uow.cards.create(
                deck_id=deck_id,
                word=parsed_card.headword,
                definition="\n".join(definition_parts),
                examples="\n".join(examples_parts) if examples_parts else None,
                next_review_date=datetime.now(UTC),
            )

    async def get_due_cards(self, deck_id: int, limit: int = 20) -> Sequence[Card]:
        async with self._uow:
            return await self._uow.cards.get_due_cards(deck_id, limit)

    async def get_card_by_id(self, card_id: int) -> Card | None:
        async with self._uow:
            return await self._uow.cards.get_by_id(card_id)

    async def review_card(self, card_id: int, quality: int) -> Card:
        async with self._uow:
            card = await self._uow.cards.get_by_id(card_id)
            if card is None:
                raise ValueError(f"Card {card_id} not found")

            ease, interval, repetitions, next_review = self._sm2.calculate(
                ease=card.ease_factor,
                interval=card.interval,
                repetitions=card.repetitions,
                quality=quality,
            )

            return await self._uow.cards.update(
                card_id,
                ease_factor=ease,
                interval=interval,
                repetitions=repetitions,
                next_review_date=next_review,
                is_new=False,
            )
