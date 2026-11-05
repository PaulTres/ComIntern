"""Check that an upload's first bytes match its extension, so a renamed file (an .exe called
report.pdf) is refused. It is not a malware scan."""

import codecs

ZIP_SIGNATURE = b"PK\x03\x04"
OLE2_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
SIGNATURES = {
    ".pdf": b"%PDF-",
    ".docx": ZIP_SIGNATURE,
    ".xlsx": ZIP_SIGNATURE,
    ".pptx": ZIP_SIGNATURE,
    ".doc": OLE2_SIGNATURE,
    ".xls": OLE2_SIGNATURE,
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}
TEXT_EXTENSIONS = {".txt", ".md", ".csv"}
HEAD_BYTES = 2048


def content_matches_extension(suffix: str, content: bytes) -> bool:
    """
    :param suffix: The file's extension, lowercase with the dot, e.g. ".pdf".
    :param content: The file's content.
    :return: True when the content starts like a file of that type.
    """
    head = content[:HEAD_BYTES]
    if suffix in TEXT_EXTENSIONS:
        if b"\x00" in head:
            return False
        try:
            # final=False tolerates a multi-byte character cut by the HEAD_BYTES boundary.
            codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
        except UnicodeDecodeError:
            return False
        return True
    signature = SIGNATURES.get(suffix)
    return signature is not None and head.startswith(signature)
