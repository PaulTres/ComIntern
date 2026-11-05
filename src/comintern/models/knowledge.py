"""Passages in the knowledge base, and what the answer chains are given."""

from enum import StrEnum

from pydantic import BaseModel, Field

PUBLIC_COMPANY_ID = 0
"""The company id stored on passages every company may read: the catalog and the official texts."""


class PassageKind(StrEnum):
    """Where a passage comes from."""

    CATALOG = "catalog"
    REGULATION_TEXT = "regulation_text"
    EVIDENCE = "evidence"


class Chunk(BaseModel):
    """One retrieved passage."""

    source_id: str = Field(
        description="The text it was cut from, e.g. evidence:42 or catalog:EU_GDPR."
    )
    title: str = Field(description="The title shown as the source, e.g. the file name.")
    chunk_index: int = Field(description="Its position in the source.")
    text: str = Field(description="The passage itself.")
    score: float = Field(description="How close it is to the query, from 0 to 1.")


class ConversationTurn(BaseModel):
    """An earlier question of the conversation and the answer it got."""

    question: str
    answer: str
