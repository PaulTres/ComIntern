"""Unit tests for validation.py: sanitisation, questionnaire and document rules."""
import pytest

import config
from domain.models import DocumentMeta
from logic.validation import (
    get_extension,
    safe_filename,
    sanitize_single_line,
    sanitize_text,
    validate_documents,
    validate_profile,
)

VALID_FORM = {
    "company_name": "Acme Ltd",
    "contact_email": "ana@acme.com",
    "industry": config.INDUSTRIES[0],
    "company_size": config.COMPANY_SIZES[1],
    "country": "Romania",
    "website": "https://acme.com",
    "primary_goal": "Reconcile supplier contracts against policy.",
    "data_sensitivity": config.DATA_SENSITIVITY[1],
    "consent": True,
}


def form(**overrides):
    return {**VALID_FORM, **overrides}


# ---- sanitisation ---------------------------------------------------------
def test_sanitize_text_strips_control_and_invisible_chars():
    assert sanitize_text("  Hi\x00 there\u202e\u200b!\n ") == "Hi there!"


def test_sanitize_text_keeps_newlines_and_tabs_and_handles_none():
    assert sanitize_text("a\n\tb") == "a\n\tb"
    assert sanitize_text(None) == ""


def test_sanitize_single_line_collapses_whitespace():
    assert sanitize_single_line("  Acme \n  Ltd ") == "Acme Ltd"


# ---- profile --------------------------------------------------------------
def test_valid_profile_passes_and_is_sanitised():
    profile, errors = validate_profile(form(company_name="  Acme\x00  Ltd "))
    assert errors == []
    assert profile.company_name == "Acme Ltd"


def test_website_is_optional():
    profile, errors = validate_profile(form(website=""))
    assert errors == [] and profile.website == ""


@pytest.mark.parametrize("field", ["company_name", "contact_email", "country", "primary_goal"])
def test_required_text_fields(field):
    profile, errors = validate_profile(form(**{field: ""}))
    assert profile is None and errors


@pytest.mark.parametrize("email", ["nope", "a@b", "a b@c.com", "a@@b.com", "@b.com"])
def test_invalid_emails_rejected(email):
    _, errors = validate_profile(form(contact_email=email))
    assert any("email" in e.lower() for e in errors)


def test_overlong_email_rejected():
    _, errors = validate_profile(form(contact_email="a" * 250 + "@b.com"))
    assert any("email" in e.lower() for e in errors)


@pytest.mark.parametrize("field", ["industry", "company_size", "data_sensitivity"])
def test_selects_must_come_from_allow_list(field):
    _, errors = validate_profile(form(**{field: "<script>"}))
    assert errors
    _, errors = validate_profile(form(**{field: None}))
    assert errors


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://x.com", "example.com", "http://", "https://[bad"])
def test_bad_websites_rejected(url):
    _, errors = validate_profile(form(website=url))
    assert any("website" in e.lower() for e in errors)


def test_consent_must_be_exactly_true():
    for value in (False, None, "on", 1):
        _, errors = validate_profile(form(consent=value))
        assert any("allowed to share" in e for e in errors)


def test_length_limits_enforced():
    _, errors = validate_profile(form(company_name="x" * (config.COMPANY_NAME_MAX + 1)))
    assert any("at most" in e for e in errors)
    _, errors = validate_profile(form(primary_goal="short"))
    assert any("at least" in e for e in errors)


def test_all_errors_reported_together():
    _, errors = validate_profile({})
    assert len(errors) >= 6


# ---- filenames ------------------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\x\\report.pdf", "report.pdf"),
        ("..hidden.pdf", "hidden.pdf"),
        ("my file (1).pdf", "my_file_1_.pdf"),
        ("**.pdf", "pdf"),
        ("", "document"),
        ("../", "document"),
    ],
)
def test_safe_filename(raw, expected):
    assert safe_filename(raw) == expected


def test_safe_filename_truncates_but_keeps_extension():
    result = safe_filename("a" * 300 + ".pdf")
    assert len(result) == 100 and result.endswith(".pdf")


def test_get_extension():
    assert get_extension("Report.PDF") == "pdf"
    assert get_extension("noext") == ""
    assert get_extension("trailing.") == ""
    assert get_extension("a.pdf.exe") == "exe"


# ---- documents ------------------------------------------------------------
PDF = DocumentMeta("a.pdf", 100, b"%PDF-1.7 rest")


def test_valid_documents_pass():
    docs = [
        PDF,
        DocumentMeta("b.docx", 10, b"PK\x03\x04..."),
        DocumentMeta("c.xlsx", 10, b"PK\x03\x04..."),
        DocumentMeta("d.csv", 10, b"a,b\n1,2"),
        DocumentMeta("e.txt", 10, "héllo".encode()),
    ]
    assert validate_documents(docs) == []


def test_no_documents_rejected():
    assert validate_documents([]) == ["Upload at least one document."]


def test_too_many_documents_rejected():
    errors = validate_documents([PDF] * (config.MAX_FILES + 1))
    assert any("at most" in e for e in errors)


def test_unsupported_extension_and_disguised_file():
    errors = validate_documents([DocumentMeta("x.exe", 10, b"MZ")])
    assert "unsupported" in errors[0]
    errors = validate_documents([DocumentMeta("fake.pdf", 10, b"MZ\x90\x00")])
    assert "do not look like" in errors[0]


def test_empty_and_oversized_files():
    assert "empty" in validate_documents([DocumentMeta("a.pdf", 0, b"")])[0]
    big = config.MAX_FILE_SIZE_MB * 1024 * 1024 + 1
    assert "larger than" in validate_documents([DocumentMeta("a.pdf", big, b"%PDF-")])[0]


def test_total_size_limit():
    each = config.MAX_FILE_SIZE_MB * 1024 * 1024
    docs = [DocumentMeta(f"{i}.pdf", each, b"%PDF-") for i in range(5)]  # 125 MB > 100 MB
    assert any("together" in e for e in validate_documents(docs))


def test_text_file_with_nul_or_invalid_utf8_rejected():
    assert validate_documents([DocumentMeta("a.txt", 5, b"ab\x00cd")])
    assert validate_documents([DocumentMeta("a.csv", 5, b"\xff\xfe\xfa")])


def test_text_head_cut_mid_character_is_accepted():
    truncated = "é".encode()[:1]  # first byte of a 2-byte character
    assert validate_documents([DocumentMeta("a.txt", 5, b"abc" + truncated)]) == []


def test_error_messages_do_not_echo_unsafe_filenames():
    errors = validate_documents([DocumentMeta("[click](http://evil)<b>.exe", 5, b"")])
    assert "<" not in errors[0] and "(" not in errors[0] and "[" not in errors[0]
