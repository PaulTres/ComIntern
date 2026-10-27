import pytest

from comintern.helpers.file_signature import content_matches_extension


@pytest.mark.parametrize(
    ("suffix", "content", "expected"),
    [
        (".pdf", b"%PDF-1.7 ...", True),
        (".pdf", b"MZ\x90\x00 an executable", False),
        (".docx", b"PK\x03\x04 zip", True),
        (".txt", "Größe și țară".encode(), True),
        (".csv", b"a,b\x00c", False),
        (".exe", b"MZ", False),
    ],
)
def test_content_matches_extension(suffix: str, content: bytes, expected: bool) -> None:
    assert content_matches_extension(suffix, content) is expected
