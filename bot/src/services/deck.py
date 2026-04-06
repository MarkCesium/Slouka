from collections.abc import Sequence
from typing import Any

from src.core.exceptions import DeckAccessDeniedError, EntityNotFoundError
from src.infra.db.models import Deck
from src.infra.db.uow import UnitOfWork


class DeckService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def _verify_deck_owner(self, deck_id: int, user_id: int) -> Deck:
        """Verify deck exists and belongs to the user. Must be called inside UoW context."""
        deck = await self._uow.decks.get_by_id(deck_id)
        if deck is None:
            raise EntityNotFoundError(f"Deck {deck_id} not found")
        if deck.user_id != user_id:
            raise DeckAccessDeniedError(f"Deck {deck_id} does not belong to user {user_id}")
        return deck

    async def get_user_decks(self, user_id: int) -> Sequence[Deck]:
        async with self._uow:
            return await self._uow.decks.get_all(user_id=user_id)

    async def create_deck(self, user_id: int, name: str) -> Deck:
        async with self._uow:
            return await self._uow.decks.create(user_id=user_id, name=name)

    async def get_deck_stats(self, deck_id: int, user_id: int) -> dict[str, int]:
        async with self._uow:
            await self._verify_deck_owner(deck_id, user_id)
            total, new, due = await self._uow.decks.get_single_deck_stats(deck_id)
            return {"total": total, "new": new, "due": due}

    async def get_decks_with_stats(self, user_id: int) -> list[dict[str, Any]]:
        """Get all decks for a user with stats in a single query."""
        async with self._uow:
            rows = await self._uow.decks.get_decks_with_stats(user_id)
            return [
                {
                    "id": deck.id,
                    "name": deck.name,
                    "total": total,
                    "new": new,
                    "due": due,
                    "to_review": new + due,
                }
                for deck, total, new, due in rows
            ]

    async def get_due_decks(self, user_id: int) -> list[dict[str, Any]]:
        """Get only decks that have cards due for review."""
        all_decks = await self.get_decks_with_stats(user_id)
        return [d for d in all_decks if d["to_review"] > 0]

    async def get_deck_by_id(self, deck_id: int, user_id: int) -> Deck:
        async with self._uow:
            return await self._verify_deck_owner(deck_id, user_id)

    async def rename_deck(self, deck_id: int, new_name: str, user_id: int) -> Deck:
        async with self._uow:
            await self._verify_deck_owner(deck_id, user_id)
            return await self._uow.decks.update(deck_id, name=new_name)

    async def delete_deck(self, deck_id: int, user_id: int) -> None:
        async with self._uow:
            await self._verify_deck_owner(deck_id, user_id)
            await self._uow.decks.delete(deck_id)
