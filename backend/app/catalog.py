"""Loads the regulation catalog, questionnaire and updates from YAML and seeds the DB."""

from functools import cache
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Regulation, RegulatoryUpdate, Requirement

DATA_DIR = Path(__file__).parent / "data"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@cache
def questionnaire() -> dict:
    return _load(DATA_DIR / "questionnaire.yaml")


def regulation_entries() -> list[dict]:
    entries = []
    for path in sorted((DATA_DIR / "regulations").glob("*.yaml")):
        entries.extend(_load(path).get("regulations", []))
    return entries


def seed(db: Session) -> None:
    """Upsert regulations, requirements and updates (idempotent, keyed by code/key)."""
    for entry in regulation_entries():
        reg = db.scalar(select(Regulation).where(Regulation.code == entry["code"]))
        if reg is None:
            reg = Regulation(code=entry["code"])
            db.add(reg)
        for field in ("name", "short_name", "jurisdiction", "category", "summary", "authority", "source_url"):
            setattr(reg, field, entry.get(field))
        reg.summary = " ".join(reg.summary.split())
        reg.applicability = entry.get("applicability", {})

        existing = {r.key: r for r in reg.requirements}
        for position, item in enumerate(entry.get("requirements", [])):
            req = existing.get(item["key"])
            if req is None:
                req = Requirement(key=item["key"])
                reg.requirements.append(req)
            req.position = position
            req.title = item["title"]
            req.description = item["description"]
            req.reference = item.get("reference")
            req.weight = item.get("weight", 1)
            req.evidence_hint = item.get("evidence_hint")

    for item in _load(DATA_DIR / "updates.yaml").get("updates", []):
        upd = db.scalar(select(RegulatoryUpdate).where(RegulatoryUpdate.key == item["key"]))
        if upd is None:
            upd = RegulatoryUpdate(key=item["key"])
            db.add(upd)
        for field in ("regulation_code", "title", "published_on", "effective_on", "kind", "severity", "source_url"):
            setattr(upd, field, item.get(field))
        upd.summary = " ".join(item["summary"].split())
    db.commit()
