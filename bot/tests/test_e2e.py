from src.core.sm2 import SM2Service
from src.infra.db.uow import UnitOfWork
from src.infra.schemas.verbum import ParsedCard, ParsedDefinition
from src.services.card import CardService
from src.services.deck import DeckService
from src.services.notification import NotificationService
from src.services.user import UserService


def _make_parsed_card(headword: str = "тэст") -> ParsedCard:
    return ParsedCard(
        headword=headword,
        definitions=[ParsedDefinition(number=1, text="значэнне", examples=["прыклад"])],
        raw_html="<p>test</p>",
        dictionary_id="tsblm2022",
    )


class TestFullCardLifecycle:
    async def test_create_review_disappear(self, uow: UnitOfWork) -> None:
        sm2 = SM2Service()
        user_service = UserService(uow)
        deck_service = DeckService(uow)
        card_service = CardService(uow, sm2)

        # Create user and deck
        user, _ = await user_service.get_or_create_user(1, "Test")
        deck = await deck_service.create_deck(user.id, "My Deck")

        # Create card
        card = await card_service.create_card(deck.id, _make_parsed_card())
        assert card is not None

        # Card appears in due list
        due = await card_service.get_due_cards(deck.id)
        assert any(c.id == card.id for c in due)

        # Review with quality=5
        reviewed = await card_service.review_card(card.id, quality=5)
        assert reviewed.is_new is False
        assert reviewed.interval >= 1

        # Card no longer in due list (next_review_date is in the future)
        due_after = await card_service.get_due_cards(deck.id)
        assert not any(c.id == card.id for c in due_after)


class TestDeduplicationAcrossService:
    async def test_duplicate_returns_none(self, uow: UnitOfWork) -> None:
        user_service = UserService(uow)
        deck_service = DeckService(uow)
        card_service = CardService(uow, SM2Service())

        user, _ = await user_service.get_or_create_user(1, "Test")
        deck = await deck_service.create_deck(user.id, "Deck")

        card1 = await card_service.create_card(deck.id, _make_parsed_card("слова"))
        card2 = await card_service.create_card(deck.id, _make_parsed_card("слова"))
        assert card1 is not None
        assert card2 is None

        # Original unchanged
        fetched = await card_service.get_card_by_id(card1.id)
        assert fetched is not None
        assert fetched.word == "слова"


class TestNotificationEligibility:
    async def test_eligible_then_disabled(self, uow: UnitOfWork) -> None:
        user_service = UserService(uow)
        deck_service = DeckService(uow)
        card_service = CardService(uow, SM2Service())
        notif_service = NotificationService(uow)

        # Create user with notifications enabled
        user, _ = await user_service.get_or_create_user(1, "Test")
        await user_service.complete_onboarding(user.id)
        deck = await deck_service.create_deck(user.id, "Deck")
        await card_service.create_card(deck.id, _make_parsed_card())

        # Should be eligible
        users = await notif_service.get_users_to_notify()
        assert any(u.id == user.id for u in users)

        # Disable notifications
        await notif_service.disable_notifications(user.id)

        # No longer eligible
        users_after = await notif_service.get_users_to_notify()
        assert not any(u.id == user.id for u in users_after)
