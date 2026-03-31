from datetime import UTC, datetime, timedelta


class SM2Service:
    DEFAULT_EASE_FACTOR = 2.5
    DEFAULT_INTERVAL = 0
    DEFAULT_REPETITIONS = 0
    MIN_EASE_FACTOR = 1.3

    def calculate(
        self,
        ease: float,
        interval: int,
        repetitions: int,
        quality: int,
    ) -> tuple[float, int, int, datetime]:
        if quality < 3:
            repetitions = 0
            interval = 1
        else:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(interval * ease)

            repetitions += 1

        ease = ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        ease = max(self.MIN_EASE_FACTOR, ease)

        next_review = datetime.now(UTC) + timedelta(days=interval)

        return ease, interval, repetitions, next_review
