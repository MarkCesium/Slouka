from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .deck import Deck


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # tg user id
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    notification_hour: Mapped[int] = mapped_column(Integer, default=9, server_default="9")
    timezone: Mapped[str] = mapped_column(
        String(50), default="Europe/Minsk", server_default="Europe/Minsk"
    )
    decks: Mapped[list[Deck]] = relationship("Deck")
