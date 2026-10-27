"""Persist validated uploads to disk in an isolated per-job directory.

SECURITY: the client-supplied filename never decides where bytes are written.
Each job gets a directory named by a server-generated UUID, and filenames pass
through `safe_filename`. Directories are 0700 and files 0600 so other OS users
on the host cannot read confidential documents.

PRODUCTION NOTE: local disk does not scale horizontally. Swap this module for
an object store (S3/GCS/Azure Blob) with server-side encryption, a retention
policy and antivirus scanning; the function signatures can stay the same.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Iterable, Optional, Union

import config
from logic.validation import safe_filename

# Job ids are uuid4().hex. Validating the format blocks path traversal via a
# forged id, since the id becomes a directory name.
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")

BufferLike = Union[bytes, bytearray, memoryview]


def _job_dir(job_id: str, root: Optional[Path]) -> Path:
    """Resolve the directory for a job and make sure it stays inside the upload root."""
    if not _JOB_ID_RE.match(job_id):
        raise ValueError("Invalid job id")
    base = (root or config.get_upload_root()).resolve()
    path = (base / job_id).resolve()
    if base not in path.parents:  # belt and braces on top of the regex
        raise ValueError("Job directory escapes the upload root")
    return path


def save_documents(
    job_id: str,
    documents: Iterable[tuple[str, BufferLike]],
    root: Optional[Path] = None,
) -> list[Path]:
    """Write each `(original_name, data)` pair to the job directory and return the paths.

    Files are prefixed with a zero-padded index (`000_report.pdf`) so two
    uploads with the same name cannot overwrite each other. Mode "xb" refuses
    to overwrite existing files. If anything fails part-way, the whole job
    directory is removed so no half-written job is left behind.
    """
    directory = _job_dir(job_id, root)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    saved: list[Path] = []
    try:
        for index, (name, data) in enumerate(documents):
            target = directory / f"{index:03d}_{safe_filename(name)}"
            with open(target, "xb") as handle:
                handle.write(data)  # memoryview is written without an extra copy
            os.chmod(target, 0o600)
            saved.append(target)
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return saved


def delete_job_files(job_id: str, root: Optional[Path] = None) -> None:
    """Remove all stored files for a job (used for rollback and retention clean-up)."""
    shutil.rmtree(_job_dir(job_id, root), ignore_errors=True)
