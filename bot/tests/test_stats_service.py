from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.uow import UnitOfWork
from src.services.stats import StatsService

from .conftest import create_card, create_deck, create_user


async def test_log_review_creates_record(uow: UnitOfWork, session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)
    card = await create_card(session, deck_id=deck.id)
    await session.commit()

    service = StatsService(uow)
    await service.log_review(user.id, card.id, quality=4)

    # Verify via repo
    async with uow:
        count = await uow.review_logs.count_reviews_in_range(
            user.id,
            datetime(2020, 1, 1, tzinfo=UTC),
            datetime(2030, 1, 1, tzinfo=UTC),
        )
    assert count == 1


async def test_get_deck_learned_stats(uow: UnitOfWork, session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id, name="Animals")

    # 2 learned cards, 1 new
    await create_card(session, deck_id=deck.id, word="кот", is_new=False, repetitions=3)
    await create_card(session, deck_id=deck.id, word="сабака", is_new=False, repetitions=1)
    await create_card(session, deck_id=deck.id, word="птушка", is_new=True, repetitions=0)
    await session.commit()

    service = StatsService(uow)
    stats = await service.get_deck_learned_stats(user.id)

    assert len(stats) == 1
    assert stats[0]["name"] == "Animals"
    assert stats[0]["learned"] == 2
    assert stats[0]["total"] == 3
    assert stats[0]["percent"] == 67


async def test_get_ease_distribution(uow: UnitOfWork, session: AsyncSession) -> None:
    user = await create_user(session)
    deck = await create_deck(session, user_id=user.id)

    # hard (EF < 2.0)
    await create_card(
        session,
        deck_id=deck.id,
        word="цяжкі",
        is_new=False,
        ease_factor=1.5,
        repetitions=1,
    )
    # medium (2.0 <= EF < 2.5)
    await create_card(
        session,
        deck_id=deck.id,
        word="сярэдні",
        is_new=False,
        ease_factor=2.2,
        repetitions=1,
    )
    # easy (EF >= 2.5)
    await create_card(
        session,
        deck_id=deck.id,
        word="лёгкі",
        is_new=False,
        ease_factor=2.8,
        repetitions=1,
    )
    # new card — should be excluded
    await create_card(
        session,
        deck_id=deck.id,
        word="новы",
        is_new=True,
        ease_factor=2.5,
        repetitions=0,
    )
    await session.commit()

    service = StatsService(uow)
    dist = await service.get_ease_distribution(user.id)

    assert dist == {"hard": 1, "medium": 1, "easy": 1}


async def test_empty_state(uow: UnitOfWork, session: AsyncSession) -> None:
    user = await create_user(session)
    await session.commit()

    service = StatsService(uow)
    stats = await service.get_deck_learned_stats(user.id)
    dist = await service.get_ease_distribution(user.id)
    counts = await service.get_review_counts(user.id, "UTC")

    assert stats == []
    assert dist == {"hard": 0, "medium": 0, "easy": 0}
    assert counts == {"week": 0, "month": 0}
