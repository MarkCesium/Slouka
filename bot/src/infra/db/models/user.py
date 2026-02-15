from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .deck import Deck


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # tg user id
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    decks: Mapped[list["Deck"]] = relationship("Deck")
