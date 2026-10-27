"""Plain data containers shared between the UI, validation and processing layers.

Frozen dataclasses make validated data immutable, so once a profile has passed
validation no later code can accidentally mutate it before processing.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyProfile:
    """Sanitised, validated answers from the questionnaire."""

    company_name: str
    contact_email: str
    industry: str
    company_size: str
    country: str
    website: str          # empty string when not provided
    primary_goal: str
    data_sensitivity: str


@dataclass(frozen=True)
class DocumentMeta:
    """What validation needs to know about an upload, without holding the whole file.

    `head` is only the first few KB, which is enough to check the file signature
    while avoiding an extra full copy of potentially large uploads in memory.
    """

    name: str
    size: int
    head: bytes
