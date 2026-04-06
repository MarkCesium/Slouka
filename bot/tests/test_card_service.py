import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DeckAccessDeniedError, EntityNotFoundError
from src.core.sm2 import SM2Service
from src.infra.db.uow import UnitOfWork
from src.infra.schemas.verbum import ParsedCard, ParsedDefinition
from src.services.card import CardService

from .conftest import create_card, create_deck, create_user


def _make_parsed_card(
    *,
    headword: str = "тэст",
    definitions: list[ParsedDefinition] | None = None,
) -> ParsedCard:
    if definitions is None:
        definitions = [
            ParsedDefinition(number=1, text="першае", examples=["прыклад1"]),
            ParsedDefinition(number=2, text="другое", examples=["прыклад2", "прыклад3"]),
        ]
    return ParsedCard(
        headword=headword,
        definitions=definitions,
        raw_html="<p>test</p>",
        dictionary_id="tsblm2022",
    )


class TestCardServiceCreate:
    async def test_creates_card(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None
        assert card.word == "тэст"
        assert card.is_new is True

    async def test_deduplication(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card1 = await service.create_card(deck.id, _make_parsed_card(), user.id)
        card2 = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card1 is not None
        assert card2 is None

    async def test_definition_concatenation(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None
        assert "1. першае" in card.definition
        assert "2. другое" in card.definition

    async def test_examples_concatenation(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None
        assert card.examples is not None
        assert "прыклад1" in card.examples
        assert "прыклад2" in card.examples
        assert "прыклад3" in card.examples

    async def test_unique_constraint_prevents_duplicate(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        """When a duplicate is inserted concurrently (bypassing find-check),
        IntegrityError is caught and None is returned."""
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await create_card(session, deck_id=deck.id, word="тэст")
        await session.commit()

        service = CardService(uow, SM2Service())
        result = await service.create_card(deck.id, _make_parsed_card(headword="тэст"), user.id)
        assert result is None


class TestCardServiceOwnership:
    async def test_create_card_in_other_users_deck_raises(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        owner = await create_user(session, id=1, name="Owner")
        other = await create_user(session, id=2, name="Other")
        deck = await create_deck(session, user_id=owner.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        with pytest.raises(DeckAccessDeniedError):
            await service.create_card(deck.id, _make_parsed_card(), other.id)

    async def test_get_due_cards_other_user_raises(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        owner = await create_user(session, id=1, name="Owner")
        other = await create_user(session, id=2, name="Other")
        deck = await create_deck(session, user_id=owner.id)
        await create_card(session, deck_id=deck.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        with pytest.raises(DeckAccessDeniedError):
            await service.get_due_cards(deck.id, user_id=other.id)

    async def test_get_deck_cards_other_user_raises(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        owner = await create_user(session, id=1, name="Owner")
        other = await create_user(session, id=2, name="Other")
        deck = await create_deck(session, user_id=owner.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        with pytest.raises(DeckAccessDeniedError):
            await service.get_deck_cards(deck.id, other.id)

    async def test_count_deck_cards_other_user_raises(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        owner = await create_user(session, id=1, name="Owner")
        other = await create_user(session, id=2, name="Other")
        deck = await create_deck(session, user_id=owner.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        with pytest.raises(DeckAccessDeniedError):
            await service.count_deck_cards(deck.id, other.id)

    async def test_paginated_cards_other_user_raises(
        self, session: AsyncSession, uow: UnitOfWork
    ) -> None:
        owner = await create_user(session, id=1, name="Owner")
        other = await create_user(session, id=2, name="Other")
        deck = await create_deck(session, user_id=owner.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        with pytest.raises(DeckAccessDeniedError):
            await service.get_deck_cards_paginated(deck.id, 10, 0, other.id)

    async def test_create_card_nonexistent_deck_raises(self, uow: UnitOfWork) -> None:
        service = CardService(uow, SM2Service())
        with pytest.raises(EntityNotFoundError):
            await service.create_card(99999, _make_parsed_card(), 1)


class TestCardServiceReview:
    async def test_sm2_values_updated(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None

        reviewed = await service.review_card(card.id, quality=5)
        assert reviewed.repetitions == 1
        assert reviewed.interval == 1
        assert reviewed.ease_factor > 2.5

    async def test_card_no_longer_new(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None
        assert card.is_new is True

        reviewed = await service.review_card(card.id, quality=4)
        assert reviewed.is_new is False

    async def test_card_not_found_raises(self, uow: UnitOfWork) -> None:
        service = CardService(uow, SM2Service())
        with pytest.raises(EntityNotFoundError, match="not found"):
            await service.review_card(99999, quality=5)


class TestCardServiceReset:
    async def test_reset_progress(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()

        service = CardService(uow, SM2Service())
        card = await service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None

        # Review to change state
        await service.review_card(card.id, quality=5)

        # Reset
        reset = await service.reset_card_progress(card.id)
        assert reset.ease_factor == 2.5
        assert reset.interval == 0
        assert reset.repetitions == 0
        assert reset.is_new is True
