from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.audit import AuditMixin

if TYPE_CHECKING:
    from .card import Card
    from .user import User


class Deck(Base, AuditMixin):
    __tablename__ = "decks"
    __table_args__ = (Index("ix_decks_user_id", "user_id"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", back_populates="decks")
    cards: Mapped[list[Card]] = relationship(
        "Card", cascade="all, delete-orphan", back_populates="deck"
    )
