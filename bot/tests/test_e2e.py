from datetime import date

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
        card = await card_service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None

        # Card appears in due list
        due = await card_service.get_due_cards(deck.id, user_id=user.id)
        assert any(c.id == card.id for c in due)

        # Review with quality=5
        reviewed = await card_service.review_card(card.id, quality=5)
        assert reviewed.is_new is False
        assert reviewed.interval >= 1

        # Card no longer in due list (next_review_date is in the future)
        due_after = await card_service.get_due_cards(deck.id, user_id=user.id)
        assert not any(c.id == card.id for c in due_after)


class TestDeduplicationAcrossService:
    async def test_duplicate_returns_none(self, uow: UnitOfWork) -> None:
        user_service = UserService(uow)
        deck_service = DeckService(uow)
        card_service = CardService(uow, SM2Service())

        user, _ = await user_service.get_or_create_user(1, "Test")
        deck = await deck_service.create_deck(user.id, "Deck")

        card1 = await card_service.create_card(deck.id, _make_parsed_card("слова"), user.id)
        card2 = await card_service.create_card(deck.id, _make_parsed_card("слова"), user.id)
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
        await card_service.create_card(deck.id, _make_parsed_card(), user.id)

        # Should be eligible
        users = await notif_service.get_users_to_notify()
        assert any(u.id == user.id for u in users)

        # Disable notifications
        await notif_service.disable_notifications(user.id)

        # No longer eligible
        users_after = await notif_service.get_users_to_notify()
        assert not any(u.id == user.id for u in users_after)


class TestStreakOnCardAdd:
    async def test_adding_card_updates_streak(self, uow: UnitOfWork) -> None:
        user_service = UserService(uow)
        deck_service = DeckService(uow)
        card_service = CardService(uow, SM2Service())

        user, _ = await user_service.get_or_create_user(1, "Test")
        deck = await deck_service.create_deck(user.id, "Deck")

        # Add card and update streak (as card_display dialog would)
        card = await card_service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None
        streak = await user_service.update_streak(user.id, date(2026, 4, 8))
        assert streak == 1

        # Same day — streak unchanged
        await card_service.create_card(deck.id, _make_parsed_card("іншае"), user.id)
        streak = await user_service.update_streak(user.id, date(2026, 4, 8))
        assert streak == 1

        # Next day — streak increments
        streak = await user_service.update_streak(user.id, date(2026, 4, 9))
        assert streak == 2


class TestStreakOnReview:
    async def test_review_continues_existing_streak(self, uow: UnitOfWork) -> None:
        user_service = UserService(uow)
        deck_service = DeckService(uow)
        card_service = CardService(uow, SM2Service())

        user, _ = await user_service.get_or_create_user(1, "Test")
        deck = await deck_service.create_deck(user.id, "Deck")
        card = await card_service.create_card(deck.id, _make_parsed_card(), user.id)
        assert card is not None

        # Build up a 5-day streak (Apr 4–8)
        for i in range(5):
            await user_service.update_streak(user.id, date(2026, 4, 4 + i))

        # Next day: review a card and update streak
        next_day = date(2026, 4, 9)
        await card_service.review_card(card.id, quality=4)
        streak = await user_service.update_streak(user.id, next_day)
        assert streak == 6

        async with uow:
            fresh_user = await uow.users.get_by_id(user.id)
            assert fresh_user is not None
            assert fresh_user.current_streak == 6
            assert fresh_user.longest_streak == 6
            assert fresh_user.last_activity_date == next_day
