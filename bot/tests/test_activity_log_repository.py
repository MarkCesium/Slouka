from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.activity import ActivityType
from src.infra.db.repositories.activity_log import ActivityLogRepository

from .conftest import create_activity_log, create_card, create_deck, create_user


async def test_get_active_days_basic(session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    await create_activity_log(
        session,
        user_id=user.id,
        card_id=card.id,
        created_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
    )
    await create_activity_log(
        session,
        user_id=user.id,
        card_id=card.id,
        created_at=datetime(2026, 4, 10, 18, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ActivityLogRepository(session)
    days = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert days == {5, 10}


async def test_get_active_days_timezone_boundary(session: AsyncSession) -> None:
    """A review at 23:30 UTC should be April 1 in UTC but April 2 in UTC+3."""
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    await create_activity_log(
        session,
        user_id=user.id,
        card_id=card.id,
        created_at=datetime(2026, 4, 1, 23, 30, tzinfo=UTC),
    )
    await session.commit()

    repo = ActivityLogRepository(session)

    days_utc = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert 1 in days_utc

    days_minsk = await repo.get_active_days(user.id, 2026, 4, "Europe/Minsk")
    assert 2 in days_minsk
    assert 1 not in days_minsk


async def test_get_active_days_empty(session: AsyncSession) -> None:
    user = await create_user(session)
    repo = ActivityLogRepository(session)
    days = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert days == set()


async def test_count_reviews_in_range(session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    for day in [5, 10, 15]:
        await create_activity_log(
            session,
            user_id=user.id,
            card_id=card.id,
            created_at=datetime(2026, 4, day, 12, 0, tzinfo=UTC),
        )
    await create_activity_log(
        session,
        user_id=user.id,
        card_id=card.id,
        created_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ActivityLogRepository(session)
    count = await repo.count_reviews_in_range(
        user.id,
        datetime(2026, 4, 1, tzinfo=UTC),
        datetime(2026, 5, 1, tzinfo=UTC),
    )
    assert count == 3


async def test_count_reviews_user_isolation(session: AsyncSession) -> None:
    user1 = await create_user(session, id=100001)
    user2 = await create_user(session, id=100002)
    deck = await create_deck(session, user_id=user1.id)
    card = await create_card(session, deck_id=deck.id)

    await create_activity_log(
        session,
        user_id=user1.id,
        card_id=card.id,
        created_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ActivityLogRepository(session)
    count1 = await repo.count_reviews_in_range(
        user1.id,
        datetime(2026, 4, 1, tzinfo=UTC),
        datetime(2026, 5, 1, tzinfo=UTC),
    )
    count2 = await repo.count_reviews_in_range(
        user2.id,
        datetime(2026, 4, 1, tzinfo=UTC),
        datetime(2026, 5, 1, tzinfo=UTC),
    )
    assert count1 == 1
    assert count2 == 0


async def test_card_added_counts_as_active_day(session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    await create_activity_log(
        session,
        user_id=user.id,
        card_id=card.id,
        activity_type=ActivityType.CARD_ADDED,
        quality=None,
        created_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ActivityLogRepository(session)
    days = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert 7 in days
