from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.repositories.review_log import ReviewLogRepository

from .conftest import create_card, create_deck, create_review_log, create_user


async def test_get_active_days_basic(session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    # Reviews on April 5 and April 10, 2026
    await create_review_log(
        session,
        user_id=user.id,
        card_id=card.id,
        reviewed_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
    )
    await create_review_log(
        session,
        user_id=user.id,
        card_id=card.id,
        reviewed_at=datetime(2026, 4, 10, 18, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ReviewLogRepository(session)
    days = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert days == {5, 10}


async def test_get_active_days_timezone_boundary(session: AsyncSession) -> None:
    """A review at 23:30 UTC should be April 1 in UTC but April 2 in UTC+3."""
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    await create_review_log(
        session,
        user_id=user.id,
        card_id=card.id,
        reviewed_at=datetime(2026, 4, 1, 23, 30, tzinfo=UTC),
    )
    await session.commit()

    repo = ReviewLogRepository(session)

    # In UTC it's April 1
    days_utc = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert 1 in days_utc

    # In Europe/Minsk (UTC+3) it's April 2
    days_minsk = await repo.get_active_days(user.id, 2026, 4, "Europe/Minsk")
    assert 2 in days_minsk
    assert 1 not in days_minsk


async def test_get_active_days_empty(session: AsyncSession) -> None:
    user = await create_user(session)
    repo = ReviewLogRepository(session)
    days = await repo.get_active_days(user.id, 2026, 4, "UTC")
    assert days == set()


async def test_count_reviews_in_range(session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)

    # 3 reviews in range, 1 outside
    for day in [5, 10, 15]:
        await create_review_log(
            session,
            user_id=user.id,
            card_id=card.id,
            reviewed_at=datetime(2026, 4, day, 12, 0, tzinfo=UTC),
        )
    await create_review_log(
        session,
        user_id=user.id,
        card_id=card.id,
        reviewed_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ReviewLogRepository(session)
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

    await create_review_log(
        session,
        user_id=user1.id,
        card_id=card.id,
        reviewed_at=datetime(2026, 4, 5, 12, 0, tzinfo=UTC),
    )
    await session.commit()

    repo = ReviewLogRepository(session)
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
