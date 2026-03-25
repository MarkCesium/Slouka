import logging

from src.infra.schemas.verbum import ParsedCard
from src.infra.verbum.client import VerbumClient
from src.infra.verbum.parser import VerbumParser

logger = logging.getLogger(__name__)


class VerbumService:
    def __init__(self, client: VerbumClient, parser: VerbumParser) -> None:
        self._client = client
        self._parser = parser

    async def search_word(self, word: str) -> list[ParsedCard]:
        response = await self._client.search(word)

        cards: list[ParsedCard] = []
        for article in response.Articles:
            parsed = self._parser.parse_article(article.Content, article.DictionaryID)
            if parsed.headword:
                cards.append(parsed)

        logger.debug("Parsed %d cards for word '%s'", len(cards), word)
        return cards
