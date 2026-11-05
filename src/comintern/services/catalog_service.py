"""Load the YAML catalog into the database, and the catalog and official texts into the knowledge base."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from comintern import catalog
from comintern.database.session_factory import SessionFactory
from comintern.helpers.text_extraction import extract_text
from comintern.models.knowledge import PassageKind
from comintern.repositories.regulation_repository import RegulationRepository
from comintern.repositories.update_repository import UpdateRepository
from comintern.schemas import Regulation, RegulatoryUpdate, Requirement
from comintern.services.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

REGULATION_FIELDS = (
    "name",
    "short_name",
    "jurisdiction",
    "category",
    "authority",
    "source_url",
)
UPDATE_FIELDS = (
    "regulation_code",
    "title",
    "published_on",
    "effective_on",
    "kind",
    "severity",
    "source_url",
)
REGULATION_TEXT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def describe_regulation(entry: dict[str, Any]) -> str:
    """
    :param entry: A regulation from the YAML catalog.
    :return: The regulation and its requirements as plain text, for the knowledge base.
    """
    lines = [
        f"{entry['name']} ({entry['short_name']}), jurisdiction {entry['jurisdiction']}, category {entry['category']}.",
        f"Authority: {entry.get('authority') or 'not specified'}. Official source: {entry.get('source_url') or 'not specified'}.",
        " ".join(entry["summary"].split()),
        "Who it applies to: "
        + " ".join(
            trigger["reason"]
            for trigger in entry.get("applicability", {}).get("triggers", [])
        ),
        "Requirements:",
    ]
    for requirement in entry.get("requirements", []):
        lines.append(
            f"- {requirement['title']} ({requirement.get('reference') or 'no reference'}): {requirement['description']} "
            f"Evidence: {requirement.get('evidence_hint') or 'not specified'}."
        )
    return "\n".join(lines)


class CatalogService:
    """Keeps the database and the knowledge base in line with the YAML catalog."""

    def __init__(
        self,
        session_factory: SessionFactory,
        knowledge_base: KnowledgeBase,
        regulation_texts_directory: Path,
    ) -> None:
        self._session_factory = session_factory
        self._knowledge_base = knowledge_base
        self._regulation_texts_directory = regulation_texts_directory

    async def seed(self) -> None:
        """Upsert regulations, requirements and updates, keyed by code and key. Safe to run again."""
        async with self._session_factory.get_session() as session:
            regulations = RegulationRepository(session)
            for entry in catalog.regulation_entries():
                regulation = await regulations.get_by_code(entry["code"])
                if regulation is None:
                    regulation = Regulation(code=entry["code"], requirements=[])
                    await regulations.add(regulation)
                for field in REGULATION_FIELDS:
                    setattr(regulation, field, entry.get(field))
                regulation.summary = " ".join(entry["summary"].split())
                regulation.applicability = entry.get("applicability", {})
                existing = {
                    requirement.key: requirement
                    for requirement in regulation.requirements
                }
                for position, item in enumerate(entry.get("requirements", [])):
                    requirement = existing.get(item["key"])
                    if requirement is None:
                        requirement = Requirement(key=item["key"])
                        regulation.requirements.append(requirement)
                    requirement.position = position
                    requirement.title = item["title"]
                    requirement.description = item["description"]
                    requirement.reference = item.get("reference")
                    requirement.weight = item.get("weight", 1)
                    requirement.evidence_hint = item.get("evidence_hint")

            updates = UpdateRepository(session)
            for item in catalog.update_entries():
                update = await updates.get_by_key(item["key"])
                if update is None:
                    update = RegulatoryUpdate(key=item["key"])
                    await updates.add(update)
                for field in UPDATE_FIELDS:
                    setattr(update, field, item.get(field))
                update.summary = " ".join(item["summary"].split())
        logger.info("Seeded the regulation catalog and the updates feed")

    async def index(self) -> int:
        """
        Index every catalog regulation, and every official text found under
        `<regulation_texts_directory>/<REGULATION_CODE>/`.

        :return: How many passages were stored.
        """
        passage_count = 0
        for entry in catalog.regulation_entries():
            passage_count += await self._knowledge_base.index(
                f"catalog:{entry['code']}",
                f"{entry['short_name']} (ComIntern catalog)",
                describe_regulation(entry),
                kind=PassageKind.CATALOG,
                regulation_code=entry["code"],
            )
        for path in sorted(self._regulation_texts_directory.glob("*/*")):
            if path.suffix.lower() not in REGULATION_TEXT_EXTENSIONS:
                continue
            text = await asyncio.to_thread(extract_text, path, None)
            if not text:
                logger.warning("No text could be read from %s", path)
                continue
            regulation_code = path.parent.name
            passage_count += await self._knowledge_base.index(
                f"text:{regulation_code}/{path.name}",
                path.stem,
                text,
                kind=PassageKind.REGULATION_TEXT,
                regulation_code=regulation_code,
            )
        return passage_count
