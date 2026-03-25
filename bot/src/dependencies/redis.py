from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.core.config import Settings


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_redis(self, settings: Settings) -> AsyncIterable[Redis]:
        client: Redis = Redis.from_url(settings.redis.url + "/1", decode_responses=True)

        await client.ping()  # type: ignore[misc]

        yield client

        await client.aclose()
