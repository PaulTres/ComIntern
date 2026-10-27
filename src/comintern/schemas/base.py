"""The shared registry of the ORM tables."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Enum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Every table inherits it, so Alembic sees them all in one metadata."""


def utcnow() -> datetime:
    """
    :return: The current time, timezone aware.
    """
    return datetime.now(UTC)


def enum_column(enum: type[StrEnum], name: str) -> Enum:
    """
    A native PostgreSQL enum that stores the enum's values (lowercase), not its names.

    :param enum: The Python enum.
    :param name: The PostgreSQL type name.
    :return: The column type.
    """
    return Enum(
        enum,
        name=name,
        values_callable=lambda members: [member.value for member in members],
    )
