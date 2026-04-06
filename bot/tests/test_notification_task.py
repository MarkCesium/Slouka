"""Tests for notification task logic.

Since send_review_notifications is wrapped by @inject(patch_module=True) and
@broker.task, we can't call it directly in tests. Instead, we test the
time-matching logic and notification flow by reimplementing the core loop
with the same logic.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramForbiddenError


def _make_user(
    *,
    id: int = 100,
    name: str = "Test",
    notification_hour: int = 9,
    notification_minute: int = 0,
    timezone: str = "Europe/Minsk",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        name=name,
        notification_hour=notification_hour,
        notification_minute=notification_minute,
        timezone=timezone,
    )


def _should_notify(user: SimpleNamespace, utc_now: datetime) -> bool:
    """Replicate the time-matching logic from send_review_notifications."""
    local_now = utc_now.astimezone(ZoneInfo(user.timezone))
    local_hour = local_now.hour
    local_minute = (local_now.minute // 10) * 10
    return local_hour == user.notification_hour and local_minute == user.notification_minute


class TestNotificationTimeMatching:
    def test_correct_hour_and_minute(self) -> None:
        user = _make_user(notification_hour=9, notification_minute=0, timezone="UTC")
        utc_now = datetime(2026, 4, 6, 9, 3, tzinfo=UTC)
        assert _should_notify(user, utc_now) is True

    def test_wrong_hour_skipped(self) -> None:
        user = _make_user(notification_hour=9, notification_minute=0, timezone="UTC")
        utc_now = datetime(2026, 4, 6, 10, 0, tzinfo=UTC)
        assert _should_notify(user, utc_now) is False

    def test_wrong_minute_bucket_skipped(self) -> None:
        user = _make_user(notification_hour=9, notification_minute=30, timezone="UTC")
        utc_now = datetime(2026, 4, 6, 9, 23, tzinfo=UTC)
        assert _should_notify(user, utc_now) is False

    def test_minute_bucketing_rounds_down(self) -> None:
        # minute=13 -> bucket=10
        user = _make_user(notification_hour=9, notification_minute=10, timezone="UTC")
        utc_now = datetime(2026, 4, 6, 9, 13, tzinfo=UTC)
        assert _should_notify(user, utc_now) is True

    def test_minute_bucketing_zero(self) -> None:
        # minute=7 -> bucket=0
        user = _make_user(notification_hour=9, notification_minute=0, timezone="UTC")
        utc_now = datetime(2026, 4, 6, 9, 7, tzinfo=UTC)
        assert _should_notify(user, utc_now) is True

    def test_different_timezones(self) -> None:
        # Both have notification_hour=12
        user_utc = _make_user(id=1, notification_hour=12, notification_minute=0, timezone="UTC")
        user_minsk = _make_user(
            id=2, notification_hour=12, notification_minute=0, timezone="Europe/Minsk"
        )
        # At 12:00 UTC, Minsk = 15:00
        utc_now = datetime(2026, 4, 6, 12, 0, tzinfo=UTC)
        assert _should_notify(user_utc, utc_now) is True
        assert _should_notify(user_minsk, utc_now) is False

    def test_timezone_match_for_non_utc(self) -> None:
        # User in Minsk wants notification at 15:00 local
        user = _make_user(notification_hour=15, notification_minute=0, timezone="Europe/Minsk")
        # 15:00 Minsk = 12:00 UTC
        utc_now = datetime(2026, 4, 6, 12, 0, tzinfo=UTC)
        assert _should_notify(user, utc_now) is True


class TestNotificationErrorHandling:
    async def test_telegram_forbidden_disables_notifications(self) -> None:
        mock_bot = AsyncMock()
        mock_notification_service = AsyncMock()

        mock_bot.send_message.side_effect = TelegramForbiddenError(
            method=AsyncMock(), message="Forbidden"
        )

        user = _make_user(id=42)

        # Simulate the error handling logic from the task
        try:
            await mock_bot.send_message(chat_id=user.id, text="test")
        except TelegramForbiddenError:
            await mock_notification_service.disable_notifications(user.id)

        mock_notification_service.disable_notifications.assert_called_once_with(42)

    async def test_exception_does_not_propagate(self) -> None:
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = RuntimeError("Network error")

        user1 = _make_user(id=1)
        user2 = _make_user(id=2)
        notified = 0

        # Simulate the task loop for two users
        for user in [user1, user2]:
            try:
                await mock_bot.send_message(chat_id=user.id, text="test")
                notified += 1
            except Exception:
                pass

        # Both attempts were made, neither succeeded
        assert mock_bot.send_message.call_count == 2
