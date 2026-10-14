"""Server-side validation and sanitisation.

SECURITY NOTE: everything here runs on the server and treats all input as
hostile. Widget constraints in the browser (max length, `type=` filters, select
boxes) are UX conveniences only; a crafted request can bypass all of them.

All functions are pure (no Streamlit, no I/O), which keeps them trivially
unit-testable and reusable if the UI is ever replaced by an API.
"""
from __future__ import annotations

import codecs
import re
import unicodedata
from typing import Any, Mapping, Optional, Sequence
from urllib.parse import urlparse

import config
from domain.models import CompanyProfile, DocumentMeta

# Deliberately simple email check: exactly one "@", no whitespace, a dot in the
# domain. Each class excludes "@" so the pattern cannot backtrack catastrophically
# (no ReDoS). Real deliverability is only provable by sending a confirmation email.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_MB = 1024 * 1024


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
def sanitize_text(value: Any) -> str:
    """Normalise free text and strip invisible/control characters.

    How: NFC-normalise, then drop every Unicode "C*" category character
    (control, format, surrogate, private-use, unassigned) except newline and tab.
    Why: removes NULs, ANSI escapes and bidi-override / zero-width characters
    that can spoof what a reviewer sees or break downstream parsers and logs.
    (Side effect: zero-width joiners inside emoji sequences are dropped too, an
    acceptable trade-off for a business intake form.)
    """
    if value is None:
        return ""
    normalised = unicodedata.normalize("NFC", str(value))
    cleaned = "".join(
        ch for ch in normalised if ch in "\n\t" or not unicodedata.category(ch).startswith("C")
    )
    return cleaned.strip()


def sanitize_single_line(value: Any) -> str:
    """Like `sanitize_text`, but collapses all whitespace (including newlines) to single spaces."""
    return " ".join(sanitize_text(value).split())


def _length_error(label: str, text: str, minimum: int, maximum: int) -> Optional[str]:
    """Return a user-facing message if `text` is outside [minimum, maximum] characters."""
    if len(text) < minimum:
        return f"{label} must be at least {minimum} characters."
    if len(text) > maximum:
        return f"{label} must be at most {maximum} characters."
    return None


def _valid_website(url: str) -> bool:
    """Accept only absolute http(s) URLs with a host.

    Why the scheme allow-list: blocks `javascript:`, `data:`, `file:` etc. that
    become dangerous if the URL is ever rendered as a link or fetched by a
    backend worker (SSRF-style abuse should additionally be handled wherever
    the URL is actually fetched).
    """
    if len(url) > config.URL_MAX:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname)
    except ValueError:  # urlparse raises on malformed IPv6 hosts etc.
        return False


# --------------------------------------------------------------------------- #
# Questionnaire
# --------------------------------------------------------------------------- #
def validate_profile(raw: Mapping[str, Any]) -> tuple[Optional[CompanyProfile], list[str]]:
    """Validate and sanitise the questionnaire answers.

    Returns `(profile, [])` on success or `(None, errors)` on failure. All
    problems are collected in one pass so the user can fix them together rather
    than one submit at a time.
    """
    errors: list[str] = []

    company_name = sanitize_single_line(raw.get("company_name"))
    email = sanitize_single_line(raw.get("contact_email"))
    industry = sanitize_single_line(raw.get("industry"))
    size = sanitize_single_line(raw.get("company_size"))
    country = sanitize_single_line(raw.get("country"))
    website = sanitize_single_line(raw.get("website"))
    goal = sanitize_text(raw.get("primary_goal"))
    sensitivity = sanitize_single_line(raw.get("data_sensitivity"))

    for message in (
        _length_error("Company name", company_name, config.COMPANY_NAME_MIN, config.COMPANY_NAME_MAX),
        _length_error("Country", country, config.COUNTRY_MIN, config.COUNTRY_MAX),
        _length_error("Your main goal", goal, config.GOAL_MIN, config.GOAL_MAX),
    ):
        if message:
            errors.append(message)

    if not email or len(email) > config.EMAIL_MAX or not _EMAIL_RE.match(email):
        errors.append("Enter a valid contact email, for example name@company.com.")

    # Select values are checked against the allow-lists: never trust the client.
    if industry not in config.INDUSTRIES:
        errors.append("Choose an industry from the list.")
    if size not in config.COMPANY_SIZES:
        errors.append("Choose a company size from the list.")
    if sensitivity not in config.DATA_SENSITIVITY:
        errors.append("Choose how sensitive your documents are.")

    if website and not _valid_website(website):
        errors.append("Enter the website as a full address starting with http:// or https://.")

    if raw.get("consent") is not True:
        errors.append("Confirm that you are allowed to share these documents.")

    if errors:
        return None, errors

    return (
        CompanyProfile(
            company_name=company_name,
            contact_email=email,
            industry=industry,
            company_size=size,
            country=country,
            website=website,
            primary_goal=goal,
            data_sensitivity=sensitivity,
        ),
        [],
    )


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #
def get_extension(name: str) -> str:
    """Lower-cased extension without the dot; '' if there is none (e.g. 'report' or 'report.')."""
    return name.rsplit(".", 1)[1].lower() if "." in name else ""


def safe_filename(name: str, max_length: int = 100) -> str:
    """Reduce a client-supplied filename to a harmless one.

    How: keep only the last path component (handles both / and \\ separators),
    transliterate to ASCII, replace anything outside [A-Za-z0-9._-] with "_",
    strip leading dots, and cap the length while preserving the extension.
    Why: client filenames are attacker-controlled; used raw they enable path
    traversal ("../../x"), hidden files, odd Unicode, and markdown/HTML
    injection when echoed back in messages.
    """
    base = name.replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).lstrip("._")
    if len(base) > max_length:
        stem, _, ext = base.rpartition(".")
        base = f"{stem[: max_length - len(ext) - 1]}.{ext}" if stem and ext else base[:max_length]
    return base or "document"


def _content_matches_extension(ext: str, head: bytes) -> bool:
    """Check the file signature ("magic bytes") against the claimed extension.

    This stops trivially renamed files (e.g. an .exe named report.pdf). It is NOT
    a malware scan: run antivirus on stored files in production.
    """
    if ext == "pdf":
        return head.startswith(b"%PDF-")
    if ext in ("docx", "xlsx"):
        return head.startswith(b"PK\x03\x04")  # both are ZIP containers
    if ext in ("txt", "csv"):
        if b"\x00" in head:  # NUL bytes mean binary content
            return False
        try:
            # Incremental decoder with final=False tolerates a multi-byte
            # character cut in half by the `head` slice boundary.
            codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
        except UnicodeDecodeError:
            return False
        return True
    return False


def validate_documents(documents: Sequence[DocumentMeta]) -> list[str]:
    """Validate the uploaded files' count, type, size and signature; return error messages."""
    errors: list[str] = []

    if not documents:
        return ["Upload at least one document."]
    if len(documents) > config.MAX_FILES:
        errors.append(f"Upload at most {config.MAX_FILES} documents at a time.")

    max_file_bytes = config.MAX_FILE_SIZE_MB * _MB
    total = 0
    for doc in documents:
        label = safe_filename(doc.name)  # safe to echo back to the user
        ext = get_extension(doc.name)
        total += doc.size

        if ext not in config.ALLOWED_EXTENSIONS:
            allowed = ", ".join(f".{e}" for e in config.ALLOWED_EXTENSIONS)
            errors.append(f"{label}: unsupported file type. Use one of {allowed}.")
            continue
        if doc.size <= 0:
            errors.append(f"{label}: the file is empty.")
        elif doc.size > max_file_bytes:
            errors.append(f"{label}: larger than {config.MAX_FILE_SIZE_MB} MB.")
        elif not _content_matches_extension(ext, doc.head):
            errors.append(f"{label}: the contents do not look like a .{ext} file.")

    if total > config.MAX_TOTAL_SIZE_MB * _MB:
        errors.append(f"Documents together must be smaller than {config.MAX_TOTAL_SIZE_MB} MB.")
    return errors
