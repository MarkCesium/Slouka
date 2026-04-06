from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.repositories.card import CardRepository

from .conftest import create_card, create_deck, create_user, future, past


class TestGetDueCards:
    async def _setup(self, session: AsyncSession) -> int:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)
        await session.commit()
        return deck.id

    async def test_new_cards_included(self, session: AsyncSession) -> None:
        deck_id = await self._setup(session)
        await create_card(session, deck_id=deck_id, is_new=True, word="new")
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck_id)
        assert len(cards) == 1
        assert cards[0].word == "new"

    async def test_overdue_cards_included(self, session: AsyncSession) -> None:
        deck_id = await self._setup(session)
        await create_card(
            session, deck_id=deck_id, is_new=False, next_review_date=past(3), word="overdue"
        )
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck_id)
        assert len(cards) == 1
        assert cards[0].word == "overdue"

    async def test_future_cards_excluded(self, session: AsyncSession) -> None:
        deck_id = await self._setup(session)
        await create_card(
            session, deck_id=deck_id, is_new=False, next_review_date=future(1), word="future"
        )
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck_id)
        assert len(cards) == 0

    async def test_ordering_by_next_review_date(self, session: AsyncSession) -> None:
        deck_id = await self._setup(session)
        await create_card(
            session, deck_id=deck_id, is_new=False, next_review_date=past(1), word="recent"
        )
        await create_card(
            session, deck_id=deck_id, is_new=False, next_review_date=past(3), word="older"
        )
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck_id)
        assert len(cards) == 2
        assert cards[0].word == "older"
        assert cards[1].word == "recent"

    async def test_limit_respected(self, session: AsyncSession) -> None:
        deck_id = await self._setup(session)
        for i in range(10):
            await create_card(session, deck_id=deck_id, is_new=True, word=f"card{i}")
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck_id, limit=5)
        assert len(cards) == 5

    async def test_deck_isolation(self, session: AsyncSession) -> None:
        user = await create_user(session, id=1)
        deck1 = await create_deck(session, user_id=user.id, name="Deck 1")
        deck2 = await create_deck(session, user_id=user.id, name="Deck 2")
        await create_card(session, deck_id=deck1.id, word="in_deck1")
        await create_card(session, deck_id=deck2.id, word="in_deck2")
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck1.id)
        assert len(cards) == 1
        assert cards[0].word == "in_deck1"

    async def test_mix_new_and_overdue(self, session: AsyncSession) -> None:
        deck_id = await self._setup(session)
        await create_card(session, deck_id=deck_id, is_new=True, word="new_card")
        await create_card(
            session, deck_id=deck_id, is_new=False, next_review_date=past(2), word="overdue_card"
        )
        await create_card(
            session, deck_id=deck_id, is_new=False, next_review_date=future(5), word="future_card"
        )
        await session.commit()

        repo = CardRepository(session)
        cards = await repo.get_due_cards(deck_id)
        words = [c.word for c in cards]
        assert "new_card" in words
        assert "overdue_card" in words
        assert "future_card" not in words
