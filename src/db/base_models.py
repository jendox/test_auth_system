from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = (
    "Base",
    "TimestampedBase",
)


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models with async support.

    Provides common configuration and primary key field for all entities.

    Attributes:
        id: Auto-incrementing primary key identifier
    """
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class TimestampedBase(Base):
    """
    Base class for entities requiring created and updated timestamps.

    Automatically manages creation and update timestamps for database records.

    Attributes:
        created_at: Timestamp of when the record was created
        updated_at: Timestamp of when the record was last updated
    """
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
