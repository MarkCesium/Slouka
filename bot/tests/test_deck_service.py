from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.uow import UnitOfWork
from src.services.deck import DeckService

from .conftest import create_card, create_deck, create_user, future, past


class TestGetDecksWithStats:
    async def test_transformation(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await create_card(session, deck_id=deck.id, is_new=True, word="new1")
        await create_card(
            session, deck_id=deck.id, is_new=False, next_review_date=past(1), word="due1"
        )
        await create_card(
            session, deck_id=deck.id, is_new=False, next_review_date=future(5), word="future1"
        )
        await session.commit()

        service = DeckService(uow)
        result = await service.get_decks_with_stats(user.id)
        assert len(result) == 1
        d = result[0]
        assert d["total"] == 3
        assert d["new"] == 1
        assert d["due"] == 1
        assert d["to_review"] == d["new"] + d["due"]
        assert "id" in d
        assert "name" in d


class TestGetDueDecks:
    async def test_filters_zero_review(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck1 = await create_deck(session, user_id=user.id, name="HasDue")
        deck2 = await create_deck(session, user_id=user.id, name="NoDue")
        await create_card(session, deck_id=deck1.id, is_new=True, word="card1")
        await create_card(
            session, deck_id=deck2.id, is_new=False, next_review_date=future(10), word="card2"
        )
        await session.commit()

        service = DeckService(uow)
        result = await service.get_due_decks(user.id)
        assert len(result) == 1
        assert result[0]["name"] == "HasDue"

    async def test_includes_decks_with_due(self, session: AsyncSession, uow: UnitOfWork) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await create_card(
            session, deck_id=deck.id, is_new=False, next_review_date=past(1), word="due"
        )
        await session.commit()

        service = DeckService(uow)
        result = await service.get_due_decks(user.id)
        assert len(result) == 1
        assert result[0]["to_review"] > 0
