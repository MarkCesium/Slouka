import logging

import aiohttp

from src.core.config import VerbumConfig
from src.infra.schemas.verbum import VerbumResponse

logger = logging.getLogger(__name__)

DEFAULT_DICT_IDS = ["tsblm2022"]


class VerbumClient:
    def __init__(self, config: VerbumConfig, session: aiohttp.ClientSession) -> None:
        self._base_url = config.url
        self._session = session

    async def search(
        self,
        word: str,
        dict_ids: list[str] | None = None,
        page: int = 1,
    ) -> VerbumResponse:
        if dict_ids is None:
            dict_ids = DEFAULT_DICT_IDS

        params = {
            "q": word,
            "in": ",".join(dict_ids),
            "page": str(page),
        }

        url = f"{self._base_url}/search"
        logger.debug("Searching Verbum API: %s params=%s", url, params)

        async with self._session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        return VerbumResponse.model_validate(data)
