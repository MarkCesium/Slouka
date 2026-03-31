from collections.abc import AsyncGenerator

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import Provider, Scope, provide

from src.core.config import Settings


class BotProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_bot(self, settings: Settings) -> AsyncGenerator[Bot]:
        bot = Bot(
            token=settings.telegram.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        yield bot
        await bot.session.close()
