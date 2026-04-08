import pytest

from src.core.plural import pluralize
from src.infra.tg.strings import Words


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "дзён"),
        (1, "дзень"),
        (2, "дні"),
        (3, "дні"),
        (4, "дні"),
        (5, "дзён"),
        (6, "дзён"),
        (10, "дзён"),
        (11, "дзён"),
        (12, "дзён"),
        (14, "дзён"),
        (19, "дзён"),
        (20, "дзён"),
        (21, "дзень"),
        (22, "дні"),
        (24, "дні"),
        (25, "дзён"),
        (100, "дзён"),
        (101, "дзень"),
        (102, "дні"),
        (111, "дзён"),
        (112, "дзён"),
        (121, "дзень"),
        (1000, "дзён"),
    ],
)
def test_pluralize_days(n: int, expected: str) -> None:
    assert pluralize(n, *Words.DAY) == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "картак"),
        (1, "картка"),
        (2, "карткі"),
        (4, "карткі"),
        (5, "картак"),
        (21, "картка"),
        (111, "картак"),
    ],
)
def test_pluralize_cards(n: int, expected: str) -> None:
    assert pluralize(n, *Words.CARD) == expected


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "картак"),
        (1, "картку"),
        (2, "карткі"),
        (4, "карткі"),
        (5, "картак"),
        (21, "картку"),
        (111, "картак"),
    ],
)
def test_pluralize_cards_accusative(n: int, expected: str) -> None:
    assert pluralize(n, *Words.CARD_ACC) == expected
