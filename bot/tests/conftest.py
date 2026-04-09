from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from src.core.activity import ActivityType
from src.infra.db.models import ActivityLog, Base, Card, Deck, User
from src.infra.db.uow import UnitOfWork

TRUNCATE = text("TRUNCATE TABLE activity_logs, cards, decks, users RESTART IDENTITY CASCADE")


@pytest.fixture(scope="session")
def postgres_container() -> PostgresContainer:  # type: ignore[misc]
    with PostgresContainer("postgres:17-bookworm", driver="asyncpg") as pg:
        yield pg  # type: ignore[misc]


@pytest.fixture(scope="session")
async def engine(postgres_container: PostgresContainer) -> AsyncGenerator[AsyncEngine]:
    url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg", 1)
    eng = create_async_engine(url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with session_factory() as sess:
        yield sess
        # Rollback any uncommitted state, then truncate for next test
        await sess.rollback()
        await sess.execute(TRUNCATE)
        await sess.commit()


@pytest.fixture
async def uow(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[UnitOfWork]:
    unit = UnitOfWork(session_factory)
    yield unit
    # Cleanup after UoW-committed data
    async with session_factory() as sess:
        await sess.execute(TRUNCATE)
        await sess.commit()


# --- Factory helpers ---


async def create_user(
    session: AsyncSession,
    *,
    id: int = 100000,
    name: str = "Test User",
    onboarding_completed: bool = True,
    notifications_enabled: bool = True,
    notification_hour: int = 9,
    notification_minute: int = 0,
    timezone: str = "Europe/Minsk",
) -> User:
    user = User(
        id=id,
        name=name,
        onboarding_completed=onboarding_completed,
        notifications_enabled=notifications_enabled,
        notification_hour=notification_hour,
        notification_minute=notification_minute,
        timezone=timezone,
    )
    session.add(user)
    await session.flush()
    return user


async def create_deck(
    session: AsyncSession,
    *,
    user_id: int,
    name: str = "Test Deck",
) -> Deck:
    deck = Deck(user_id=user_id, name=name)
    session.add(deck)
    await session.flush()
    return deck


async def create_card(
    session: AsyncSession,
    *,
    deck_id: int,
    word: str = "тэст",
    definition: str = "test definition",
    examples: str | None = None,
    is_new: bool = True,
    next_review_date: datetime | None = None,
    ease_factor: float = 2.5,
    interval: int = 0,
    repetitions: int = 0,
) -> Card:
    if next_review_date is None:
        next_review_date = datetime.now(UTC)
    card = Card(
        deck_id=deck_id,
        word=word,
        definition=definition,
        examples=examples,
        is_new=is_new,
        next_review_date=next_review_date,
        ease_factor=ease_factor,
        interval=interval,
        repetitions=repetitions,
    )
    session.add(card)
    await session.flush()
    return card


async def create_activity_log(
    session: AsyncSession,
    *,
    user_id: int,
    card_id: int,
    activity_type: str = ActivityType.REVIEW,
    quality: int | None = 4,
    created_at: datetime | None = None,
) -> ActivityLog:
    if created_at is None:
        created_at = datetime.now(UTC)
    log = ActivityLog(
        user_id=user_id,
        card_id=card_id,
        activity_type=activity_type,
        quality=quality,
        created_at=created_at,
    )
    session.add(log)
    await session.flush()
    return log


def past(days: int = 1) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def future(days: int = 1) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)
