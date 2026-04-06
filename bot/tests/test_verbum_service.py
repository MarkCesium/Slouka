import aiohttp
import pytest

from src.core.config import VerbumConfig
from src.infra.verbum.client import VerbumClient
from src.infra.verbum.parser import VerbumParser
from src.services.verbum import VerbumService


@pytest.fixture(scope="session")
async def verbum_service() -> VerbumService:
    config = VerbumConfig(url="https://verbum.by/api")
    async with aiohttp.ClientSession() as session:
        client = VerbumClient(config, session)
        parser = VerbumParser()
        service = VerbumService(client, parser)
        yield service  # type: ignore[misc]


class TestVerbumServiceSearch:
    async def test_existing_word_returns_results(self, verbum_service: VerbumService) -> None:
        cards = await verbum_service.search_word("слова")
        assert len(cards) > 0

    async def test_parsed_card_has_fields(self, verbum_service: VerbumService) -> None:
        cards = await verbum_service.search_word("слова")
        assert len(cards) > 0
        card = cards[0]
        assert card.headword
        assert card.dictionary_id
        assert len(card.definitions) > 0

    async def test_headword_matches_query(self, verbum_service: VerbumService) -> None:
        cards = await verbum_service.search_word("дом")
        for card in cards:
            assert card.headword.lower().replace("\u0301", "") == "дом"

    async def test_sorted_by_dictionary_priority(self, verbum_service: VerbumService) -> None:
        cards = await verbum_service.search_word("слова")
        if len(cards) >= 2:
            from src.infra.verbum.parser import DICTIONARY_PRIORITY

            priorities = [DICTIONARY_PRIORITY.get(c.dictionary_id, 99) for c in cards]
            assert priorities == sorted(priorities)

    async def test_nonexistent_word_returns_empty(self, verbum_service: VerbumService) -> None:
        cards = await verbum_service.search_word("xyzxyzxyz123")
        assert len(cards) == 0

    async def test_definition_has_text(self, verbum_service: VerbumService) -> None:
        cards = await verbum_service.search_word("хата")
        assert len(cards) > 0
        for card in cards:
            for defn in card.definitions:
                assert defn.text.strip()
