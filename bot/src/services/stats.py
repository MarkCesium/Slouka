from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from src.infra.db.uow import UnitOfWork


class StatsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def log_activity(
        self,
        user_id: int,
        card_id: int,
        activity_type: str,
        quality: int | None = None,
    ) -> None:
        async with self._uow:
            await self._uow.activity_logs.log_activity(user_id, card_id, activity_type, quality)

    async def get_calendar_data(self, user_id: int, year: int, month: int, tz: str) -> set[int]:
        async with self._uow:
            return await self._uow.activity_logs.get_active_days(user_id, year, month, tz)

    async def get_review_counts(self, user_id: int, tz: str) -> dict[str, int]:
        """Return review counts for current week (from Monday) and current month."""
        zone = ZoneInfo(tz)
        now_local = datetime.now(zone)
        today_local = now_local.date()

        # Week start: Monday
        monday = today_local - timedelta(days=today_local.weekday())
        week_start = datetime.combine(monday, time.min, tzinfo=zone)

        # Month start
        month_start = datetime.combine(today_local.replace(day=1), time.min, tzinfo=zone)

        # Convert to UTC for query
        week_start_utc = week_start.astimezone(ZoneInfo("UTC"))
        month_start_utc = month_start.astimezone(ZoneInfo("UTC"))
        now_utc = now_local.astimezone(ZoneInfo("UTC"))

        async with self._uow:
            week = await self._uow.activity_logs.count_reviews_in_range(
                user_id, week_start_utc, now_utc
            )
            month = await self._uow.activity_logs.count_reviews_in_range(
                user_id, month_start_utc, now_utc
            )
        return {"week": week, "month": month}

    async def get_ease_distribution(self, user_id: int) -> dict[str, int]:
        async with self._uow:
            return await self._uow.cards.get_ease_distribution(user_id)

    async def get_deck_learned_stats(self, user_id: int) -> list[dict[str, Any]]:
        async with self._uow:
            rows = await self._uow.cards.get_learned_stats_per_deck(user_id)
        return [
            {
                "name": row.deck_name,
                "learned": row.learned,
                "total": row.total,
                "percent": round(row.learned / row.total * 100) if row.total > 0 else 0,
            }
            for row in rows
        ]
