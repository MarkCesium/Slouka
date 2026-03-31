from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins.audit import AuditMixin, TDateTime


class Card(Base, AuditMixin):
    __tablename__ = "cards"
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
