import logging
from contextlib import AbstractAsyncContextManager
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


logger = logging.getLogger(__name__)


class UnitOfWork(AbstractAsyncContextManager["UnitOfWork"]):
    def __init__(self, async_session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session = async_session_factory()

    async def __aenter__(self) -> Self:
        logger.debug("Creating new session")
        # Repositories initialization
        return self

    async def commit(self) -> None:
        logger.debug("Committing transaction")
        await self.session.commit()

    async def rollback(self) -> None:
        logger.debug("Rolling back transaction")
        await self.session.rollback()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if exc_type:
            logger.warning(f"Exception occurred: {exc_type.__name__}: {exc_val}")
            await self.rollback()
        else:
            logger.debug("Transaction completed successfully")
            await self.commit()
        await self.session.close()
