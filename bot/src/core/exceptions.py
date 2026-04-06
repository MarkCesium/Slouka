class EntityNotFoundError(Exception):
    """Raised when a database entity is not found."""


class DeckAccessDeniedError(Exception):
    """Raised when a user tries to access a deck they don't own."""
