"""The curated data kept as YAML next to this file: the questionnaire, the regulation catalog
and the regulatory updates feed. `comintern-seed` loads it into the database."""

from functools import cache
from pathlib import Path
from typing import Any

import yaml

CATALOG_DIRECTORY = Path(__file__).parent


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@cache
def questionnaire() -> dict[str, Any]:
    """
    :return: The onboarding questionnaire: steps, questions and their show_if conditions.
    """
    return _load(CATALOG_DIRECTORY / "questionnaire.yaml")


def regulation_entries() -> list[dict[str, Any]]:
    """
    :return: Every regulation of every jurisdiction file, with its triggers and requirements.
    """
    entries: list[dict[str, Any]] = []
    for path in sorted((CATALOG_DIRECTORY / "regulations").glob("*.yaml")):
        entries.extend(_load(path).get("regulations", []))
    return entries


def update_entries() -> list[dict[str, Any]]:
    """
    :return: The regulatory updates feed.
    """
    return _load(CATALOG_DIRECTORY / "updates.yaml").get("updates", [])
