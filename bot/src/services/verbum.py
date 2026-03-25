import logging
import unicodedata

from src.infra.schemas.verbum import ParsedCard
from src.infra.verbum.client import VerbumClient
from src.infra.verbum.parser import DICTIONARY_PRIORITY, VerbumParser

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Lowercase and strip combining accent marks for comparison."""
    text = text.lower().strip()
    # Remove combining acute accent (U+0301) used for stress marks
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", text)


class VerbumService:
    def __init__(self, client: VerbumClient, parser: VerbumParser) -> None:
        self._client = client
        self._parser = parser

    async def search_word(self, word: str) -> list[ParsedCard]:
        response = await self._client.search(word)

        query_norm = _normalize(word)

        cards: list[ParsedCard] = []
        for article in response.Articles:
            parsed = self._parser.parse_article(article.Content, article.DictionaryID)
            if not parsed.headword:
                continue
            # Filter: only keep articles where headword matches the query
            if _normalize(parsed.headword) != query_norm:
                continue
            cards.append(parsed)

        # Sort by dictionary priority
        cards.sort(key=lambda c: DICTIONARY_PRIORITY.get(c.dictionary_id, 99))

        logger.debug("Parsed %d cards for word '%s'", len(cards), word)
        return cards
