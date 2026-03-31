from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from src.core.config import Settings

settings = Settings()  # type: ignore[call-arg]

broker = RedisStreamBroker(
    url=settings.redis.url + "/2",
).with_result_backend(
    RedisAsyncResultBackend(
        redis_url=settings.redis.url + "/2",
    ),
)


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    from dishka import make_async_container
    from dishka.integrations.taskiq import TaskiqProvider, setup_dishka

    from src.dependencies.bot import BotProvider
    from src.dependencies.config import ConfigProvider
    from src.dependencies.db import DBProvider
    from src.dependencies.services import ServiceProvider

    container = make_async_container(
        ConfigProvider(),
        DBProvider(),
        BotProvider(),
        ServiceProvider(),
        TaskiqProvider(),
    )
    setup_dishka(container=container, broker=broker)
