import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram_dialog import setup_dialogs
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka

from src.core.config import Settings
from src.dependencies.config import ConfigProvider
from src.dependencies.db import DBProvider
from src.dependencies.redis import RedisProvider
from src.dependencies.services import ServiceProvider
from src.infra.tg.dialogs import get_dialogs_router
from src.infra.tg.handlers.common import router as common_router
from src.infra.tg.handlers.start import router as start_router
from src.infra.tg.middlewares import UserMiddleware


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]

    logging.basicConfig(
        level=settings.logging.level_value,
        format=settings.logging.format,
        datefmt=settings.logging.date_format,
    )

    bot = Bot(
        token=settings.telegram.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(
        storage=RedisStorage.from_url(
            settings.redis.url + "/0",
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    )

    container = make_async_container(
        ConfigProvider(),
        DBProvider(),
        RedisProvider(),
        ServiceProvider(),
    )
    setup_dishka(container=container, router=dp)

    dp.update.outer_middleware(UserMiddleware())

    dp.include_router(start_router)
    dp.include_router(common_router)

    dp.include_router(get_dialogs_router())
    setup_dialogs(dp)

    try:
        logging.info("Starting Slouka bot...")
        await dp.start_polling(bot)  # pyright: ignore[reportUnknownMemberType]
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
