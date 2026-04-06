from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time

from src.core.sm2 import SM2Service


class TestSM2Calculate:
    def setup_method(self) -> None:
        self.sm2 = SM2Service()

    def test_quality_5_first_review(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(2.5, 0, 0, quality=5)
        assert reps == 1
        assert interval == 1
        assert ease == pytest.approx(2.6)

    def test_quality_5_second_review(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(2.6, 1, 1, quality=5)
        assert reps == 2
        assert interval == 6
        assert ease == pytest.approx(2.7)

    def test_quality_5_third_review(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(2.6, 6, 2, quality=5)
        assert reps == 3
        assert interval == round(6 * 2.6)  # 16
        assert ease == pytest.approx(2.7)

    def test_quality_4_neutral(self) -> None:
        # quality=4: ease delta = 0.1 - 1*(0.08 + 1*0.02) = 0
        ease, interval, reps, _ = self.sm2.calculate(2.5, 0, 0, quality=4)
        assert reps == 1
        assert interval == 1
        assert ease == pytest.approx(2.5)

    def test_quality_3_threshold(self) -> None:
        # quality=3 is pass (not reset), but ease drops
        ease, interval, reps, _ = self.sm2.calculate(2.5, 0, 0, quality=3)
        assert reps == 1  # incremented, NOT reset
        assert interval == 1
        # ease delta = 0.1 - 2*(0.08 + 2*0.02) = 0.1 - 0.24 = -0.14
        assert ease == pytest.approx(2.36)

    def test_quality_2_failure(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(2.5, 10, 5, quality=2)
        assert reps == 0  # reset
        assert interval == 1  # reset
        # ease delta = 0.1 - 3*(0.08 + 3*0.02) = 0.1 - 0.42 = -0.32
        assert ease == pytest.approx(2.18)

    def test_quality_1_bad_failure(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(2.5, 10, 5, quality=1)
        assert reps == 0
        assert interval == 1
        # ease delta = 0.1 - 4*(0.08 + 4*0.02) = 0.1 - 0.64 = -0.54
        assert ease == pytest.approx(1.96)

    def test_quality_0_total_failure(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(2.5, 10, 5, quality=0)
        assert reps == 0
        assert interval == 1
        # ease delta = 0.1 - 5*(0.08 + 5*0.02) = 0.1 - 0.9 = -0.8
        assert ease == pytest.approx(1.7)

    def test_ease_floor_at_min(self) -> None:
        # Start with low ease, quality=0 should not drop below 1.3
        ease, _, _, _ = self.sm2.calculate(1.3, 1, 0, quality=0)
        assert ease == 1.3

    def test_ease_floor_prevents_going_below(self) -> None:
        # quality=0, starting ease=1.5: delta=-0.8, raw=0.7, clamped to 1.3
        ease, _, _, _ = self.sm2.calculate(1.5, 1, 0, quality=0)
        assert ease == 1.3

    def test_repeated_failures_then_recovery(self) -> None:
        ease, interval, reps = 2.5, 0, 0
        # 3 failures
        for _ in range(3):
            ease, interval, reps, _ = self.sm2.calculate(ease, interval, reps, quality=0)
        assert reps == 0
        assert interval == 1
        assert ease == 1.3  # clamped to floor

        # 3 perfect reviews
        for _ in range(3):
            ease, interval, reps, _ = self.sm2.calculate(ease, interval, reps, quality=5)
        assert reps == 3
        assert interval > 6  # should have grown past 6

    def test_long_quality_5_progression(self) -> None:
        ease, interval, reps = 2.5, 0, 0
        intervals = []
        for _ in range(10):
            ease, interval, reps, _ = self.sm2.calculate(ease, interval, reps, quality=5)
            intervals.append(interval)
        # First=1, second=6, then exponential growth
        assert intervals[0] == 1
        assert intervals[1] == 6
        for i in range(2, len(intervals)):
            assert intervals[i] > intervals[i - 1]

    @freeze_time("2026-04-06 12:00:00", tz_offset=0)
    def test_next_review_date(self) -> None:
        _, interval, _, next_review = self.sm2.calculate(2.5, 0, 0, quality=5)
        expected = datetime(2026, 4, 6, 12, 0, 0, tzinfo=UTC) + timedelta(days=interval)
        assert abs((next_review - expected).total_seconds()) < 1

    def test_large_interval_with_low_ease(self) -> None:
        ease, interval, reps, _ = self.sm2.calculate(1.3, 365, 5, quality=3)
        assert interval == round(365 * 1.3)  # 475
        assert reps == 6
