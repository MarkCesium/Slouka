from datetime import datetime

from sqlalchemy import Integer, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db.models import ActivityLog

from .base import BaseRepository


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(ActivityLog, session)

    async def log_activity(
        self,
        user_id: int,
        card_id: int,
        activity_type: str,
        quality: int | None = None,
    ) -> ActivityLog:
        return await self.create(
            user_id=user_id,
            card_id=card_id,
            activity_type=activity_type,
            quality=quality,
        )

    async def get_active_days(self, user_id: int, year: int, month: int, tz: str) -> set[int]:
        """Return set of day-of-month integers where the user had at least one activity."""
        local_time = func.timezone(tz, ActivityLog.created_at)
        query = select(distinct(func.extract("day", local_time).cast(Integer))).where(
            ActivityLog.user_id == user_id,
            func.extract("year", local_time) == year,
            func.extract("month", local_time) == month,
        )
        result = await self.session.execute(query)
        return set(result.scalars().all())

    async def count_reviews_in_range(self, user_id: int, start: datetime, end: datetime) -> int:
        query = (
            select(func.count())
            .select_from(ActivityLog)
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.created_at >= start,
                ActivityLog.created_at < end,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()
