from collections.abc import AsyncGenerator

import aiohttp
from dishka import Provider, Scope, provide

from src.core.config import Settings
from src.core.sm2 import SM2Service
from src.infra.db.uow import UnitOfWork
from src.infra.verbum.client import VerbumClient
from src.infra.verbum.parser import VerbumParser
from src.services.card import CardService
from src.services.deck import DeckService
from src.services.user import UserService
from src.services.verbum import VerbumService


class ServiceProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_aiohttp_session(self) -> AsyncGenerator[aiohttp.ClientSession]:
        session = aiohttp.ClientSession()
        yield session
        await session.close()

    @provide(scope=Scope.APP)
    def provide_verbum_client(
        self, settings: Settings, session: aiohttp.ClientSession
    ) -> VerbumClient:
        return VerbumClient(settings.verbum, session)

    @provide(scope=Scope.APP)
    def provide_verbum_parser(self) -> VerbumParser:
        return VerbumParser()

    @provide(scope=Scope.REQUEST)
    def provide_sm2_service(self) -> SM2Service:
        return SM2Service()

    @provide(scope=Scope.REQUEST)
    def provide_verbum_service(self, client: VerbumClient, parser: VerbumParser) -> VerbumService:
        return VerbumService(client, parser)

    @provide(scope=Scope.REQUEST)
    def provide_user_service(self, uow: UnitOfWork) -> UserService:
        return UserService(uow)

    @provide(scope=Scope.REQUEST)
    def provide_deck_service(self, uow: UnitOfWork) -> DeckService:
        return DeckService(uow)

    @provide(scope=Scope.REQUEST)
    def provide_card_service(self, uow: UnitOfWork, sm2: SM2Service) -> CardService:
        return CardService(uow, sm2)
