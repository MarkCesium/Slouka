from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.audit import AuditMixin

if TYPE_CHECKING:
    from .card import Card


class Deck(Base, AuditMixin):
    __tablename__ = "decks"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    cards: Mapped[list[Card]] = relationship("Card", cascade="all, delete-orphan")
