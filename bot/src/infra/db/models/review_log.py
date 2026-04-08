from sqlalchemy import BigInteger, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins.audit import TDateTime


class ReviewLog(Base):
    __tablename__ = "review_logs"
    __table_args__ = (Index("ix_review_logs_user_reviewed", "user_id", "reviewed_at"),)

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False
    )
    quality: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_at: Mapped[TDateTime]
