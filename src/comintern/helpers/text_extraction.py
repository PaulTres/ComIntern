"""Extract plain text from evidence uploads and official regulation texts, so the assistant can search them."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_CHARS = 500_000


def extract_text(path: Path, mime_type: str | None) -> str | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf" or mime_type == "application/pdf":
            from pypdf import PdfReader

            text = "\n".join(
                page.extract_text() or "" for page in PdfReader(path).pages
            )
        elif suffix == ".docx":
            from docx import Document

            text = "\n".join(p.text for p in Document(str(path)).paragraphs)
        elif suffix in {".txt", ".md", ".csv"} or (mime_type or "").startswith("text/"):
            text = path.read_text(errors="replace")
        else:
            return None
    except Exception:
        logger.exception("Text extraction failed for %s", path.name)
        return None
    return text.strip()[:MAX_CHARS] or None
