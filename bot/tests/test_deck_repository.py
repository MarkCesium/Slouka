from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.repositories.deck import DeckRepository

from .conftest import create_card, create_deck, create_user, future, past


class TestGetDecksWithStats:
    async def test_mixed_card_states(self, session: AsyncSession) -> None:
        user = await create_user(session, id=1)
        deck = await create_deck(session, user_id=user.id)

        # 2 new, 3 overdue, 5 not-yet-due
        for i in range(2):
            await create_card(session, deck_id=deck.id, is_new=True, word=f"new{i}")
        for i in range(3):
            await create_card(
                session, deck_id=deck.id, is_new=False, next_review_date=past(1), word=f"due{i}"
            )
        for i in range(5):
            await create_card(
                session,
                deck_id=deck.id,
                is_new=False,
                next_review_date=future(5),
                word=f"future{i}",
            )
        await session.commit()

        repo = DeckRepository(session)
        rows = await repo.get_decks_with_stats(user.id)
        assert len(rows) == 1
        _, total, new, due = rows[0]
        assert total == 10
        assert new == 2
        assert due == 3

    async def test_empty_deck(self, session: AsyncSession) -> None:
        user = await create_user(session, id=1)
        await create_deck(session, user_id=user.id, name="Empty")
        await session.commit()

        repo = DeckRepository(session)
        rows = await repo.get_decks_with_stats(user.id)
        assert len(rows) == 1
        _, total, new, due = rows[0]
        assert total == 0
        assert new == 0
        assert due == 0

    async def test_multiple_decks_not_mixed(self, session: AsyncSession) -> None:
        user = await create_user(session, id=1)
        deck1 = await create_deck(session, user_id=user.id, name="Deck1")
        deck2 = await create_deck(session, user_id=user.id, name="Deck2")
        await create_card(session, deck_id=deck1.id, is_new=True, word="card1")
        await create_card(
            session, deck_id=deck2.id, is_new=False, next_review_date=past(1), word="card2"
        )
        await session.commit()

        repo = DeckRepository(session)
        rows = await repo.get_decks_with_stats(user.id)
        stats = {row[0].name: (row[1], row[2], row[3]) for row in rows}
        assert stats["Deck1"] == (1, 1, 0)  # total=1, new=1, due=0
        assert stats["Deck2"] == (1, 0, 1)  # total=1, new=0, due=1

    async def test_other_users_decks_excluded(self, session: AsyncSession) -> None:
        user1 = await create_user(session, id=1, name="User1")
        user2 = await create_user(session, id=2, name="User2")
        await create_deck(session, user_id=user1.id, name="My Deck")
        await create_deck(session, user_id=user2.id, name="Other Deck")
        await session.commit()

        repo = DeckRepository(session)
        rows = await repo.get_decks_with_stats(user1.id)
        assert len(rows) == 1
        assert rows[0][0].name == "My Deck"
