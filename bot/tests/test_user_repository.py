from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.repositories.user import UserRepository

from .conftest import create_card, create_deck, create_user, future, past


class TestGetUsersToNotify:
    async def test_eligible_user_returned(self, session: AsyncSession) -> None:
        user = await create_user(
            session, id=1, notifications_enabled=True, onboarding_completed=True
        )
        deck = await create_deck(session, user_id=user.id)
        await create_card(session, deck_id=deck.id, is_new=True)
        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        assert len(users) == 1
        assert users[0].id == 1

    async def test_notifications_disabled_excluded(self, session: AsyncSession) -> None:
        user = await create_user(
            session, id=1, notifications_enabled=False, onboarding_completed=True
        )
        deck = await create_deck(session, user_id=user.id)
        await create_card(session, deck_id=deck.id, is_new=True)
        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        assert len(users) == 0

    async def test_onboarding_not_completed_excluded(self, session: AsyncSession) -> None:
        user = await create_user(
            session, id=1, notifications_enabled=True, onboarding_completed=False
        )
        deck = await create_deck(session, user_id=user.id)
        await create_card(session, deck_id=deck.id, is_new=True)
        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        assert len(users) == 0

    async def test_no_due_cards_excluded(self, session: AsyncSession) -> None:
        user = await create_user(
            session, id=1, notifications_enabled=True, onboarding_completed=True
        )
        deck = await create_deck(session, user_id=user.id)
        await create_card(session, deck_id=deck.id, is_new=False, next_review_date=future(5))
        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        assert len(users) == 0

    async def test_no_cards_at_all_excluded(self, session: AsyncSession) -> None:
        await create_user(session, id=1, notifications_enabled=True, onboarding_completed=True)
        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        assert len(users) == 0

    async def test_empty_deck_excluded(self, session: AsyncSession) -> None:
        user = await create_user(
            session, id=1, notifications_enabled=True, onboarding_completed=True
        )
        await create_deck(session, user_id=user.id)
        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        assert len(users) == 0

    async def test_mixed_users(self, session: AsyncSession) -> None:
        # User 1: eligible
        u1 = await create_user(
            session, id=1, name="Eligible", notifications_enabled=True, onboarding_completed=True
        )
        d1 = await create_deck(session, user_id=u1.id)
        await create_card(session, deck_id=d1.id, is_new=True)

        # User 2: notifications off
        u2 = await create_user(
            session, id=2, name="NoNotif", notifications_enabled=False, onboarding_completed=True
        )
        d2 = await create_deck(session, user_id=u2.id)
        await create_card(session, deck_id=d2.id, is_new=True)

        # User 3: no due cards
        u3 = await create_user(
            session, id=3, name="NoDue", notifications_enabled=True, onboarding_completed=True
        )
        d3 = await create_deck(session, user_id=u3.id)
        await create_card(session, deck_id=d3.id, is_new=False, next_review_date=future(10))

        # User 4: eligible with overdue card
        u4 = await create_user(
            session, id=4, name="Overdue", notifications_enabled=True, onboarding_completed=True
        )
        d4 = await create_deck(session, user_id=u4.id)
        await create_card(session, deck_id=d4.id, is_new=False, next_review_date=past(2))

        await session.commit()

        repo = UserRepository(session)
        users = await repo.get_users_to_notify()
        user_ids = {u.id for u in users}
        assert user_ids == {1, 4}
