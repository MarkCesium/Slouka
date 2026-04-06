from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins.audit import AuditMixin, TDateTime

if TYPE_CHECKING:
    from .deck import Deck


class Card(Base, AuditMixin):
    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint("deck_id", "word", name="uq_cards_deck_id_word"),
        Index("ix_cards_deck_id_next_review_date", "deck_id", "next_review_date"),
        Index("ix_cards_is_new", "is_new", postgresql_where=text("is_new = true")),
    )

    word: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[str] = mapped_column(Text, nullable=True)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, server_default="2.5")
    interval: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    repetitions: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    next_review_date: Mapped[TDateTime]
    is_new: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    deck_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False
    )
    deck: Mapped[Deck] = relationship("Deck", back_populates="cards")
