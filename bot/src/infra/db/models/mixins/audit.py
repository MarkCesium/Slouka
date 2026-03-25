from datetime import UTC, datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


def now() -> datetime:
    return datetime.now(UTC)


TDateTime = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        default=now,
        server_default=func.now(),
    ),
]


class AuditMixin:
    created_at: Mapped[TDateTime]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now,
        server_default=func.now(),
        onupdate=now,
        server_onupdate=func.now(),
    )
