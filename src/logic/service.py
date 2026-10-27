"""Application logic: the one place that turns a form submission into a job.

Keeping this orchestration out of `app.py` means the whole submit flow
(validate -> store -> enqueue, with rollback) is testable without Streamlit.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence

import config
from domain.models import DocumentMeta
from logic.processing import JobManager
from persistence.storage import delete_job_files, save_documents
from logic.validation import validate_documents, validate_profile

logger = logging.getLogger(__name__)


class UploadLike(Protocol):
    """The subset of Streamlit's UploadedFile that we rely on (eases testing)."""

    name: str

    def getbuffer(self) -> memoryview: ...


@dataclass(frozen=True)
class SubmissionResult:
    """Outcome of a submission: either a job id, or user-facing error messages."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    job_id: Optional[str] = None


def submit_intake(
    raw_form: Mapping[str, Any],
    uploads: Sequence[UploadLike],
    manager: JobManager,
    upload_root: Optional[Path] = None,
) -> SubmissionResult:
    """Validate the form and files, store the files, and queue processing.

    Steps and why:
      1. Validate everything first and report all errors together, so nothing is
         written to disk for an invalid submission.
      2. Generate the job id on the server (uuid4) so it is unguessable and
         safe to use as a directory name.
      3. Store files, then enqueue. If enqueueing fails the stored files are
         deleted, so failures do not leak orphaned confidential documents.
    """
    profile, errors = validate_profile(raw_form)

    # Read each buffer once. `getbuffer` returns a memoryview, so no copy of
    # the file content is made here; only the small header is copied to bytes.
    buffers = [upload.getbuffer() for upload in uploads]
    metas = [
        DocumentMeta(name=upload.name, size=buf.nbytes, head=bytes(buf[: config.HEAD_BYTES]))
        for upload, buf in zip(uploads, buffers)
    ]
    errors += validate_documents(metas)
    if errors or profile is None:
        return SubmissionResult(ok=False, errors=errors)

    job_id = uuid.uuid4().hex
    try:
        paths = save_documents(
            job_id, ((upload.name, buf) for upload, buf in zip(uploads, buffers)), upload_root
        )
    except OSError:
        logger.exception("Could not store documents for job %s", job_id)
        return SubmissionResult(ok=False, errors=["We could not store your documents. Please try again."])

    try:
        manager.submit(job_id, profile, paths)
    except Exception:
        logger.exception("Could not enqueue job %s", job_id)
        delete_job_files(job_id, upload_root)  # roll back the stored files
        return SubmissionResult(ok=False, errors=["We could not start processing. Please try again."])

    return SubmissionResult(ok=True, job_id=job_id)
