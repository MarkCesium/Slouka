from datetime import datetime

from sqlalchemy import Integer, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import ReviewLog

from .base import BaseRepository


class ReviewLogRepository(BaseRepository[ReviewLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(ReviewLog, session)

    async def log_review(self, user_id: int, card_id: int, quality: int) -> ReviewLog:
        return await self.create(user_id=user_id, card_id=card_id, quality=quality)

    async def get_active_days(self, user_id: int, year: int, month: int, tz: str) -> set[int]:
        """Return set of day-of-month integers where the user had at least one review."""
        local_time = func.timezone(tz, ReviewLog.reviewed_at)
        query = select(distinct(func.extract("day", local_time).cast(Integer))).where(
            ReviewLog.user_id == user_id,
            func.extract("year", local_time) == year,
            func.extract("month", local_time) == month,
        )
        result = await self.session.execute(query)
        return set(result.scalars().all())

    async def count_reviews_in_range(self, user_id: int, start: datetime, end: datetime) -> int:
        query = (
            select(func.count())
            .select_from(ReviewLog)
            .where(
                ReviewLog.user_id == user_id,
                ReviewLog.reviewed_at >= start,
                ReviewLog.reviewed_at < end,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()
