"""Backend job handling: queue the work, track its status, never block the UI.

Streamlit re-runs the script on every interaction, so long work must happen
outside the script thread. `JobManager` runs jobs on a small thread pool and
exposes thread-safe status look-ups.

SCALABILITY NOTE: this in-process manager is fine for one server instance. With
multiple instances or a need to survive restarts, replace it with a real queue
(Celery / RQ / Cloud Tasks) and a shared status store (Redis / database). The
public surface (`submit`, `get_status`, `wait`) is intentionally small so that
swap stays local to this module.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Sequence

from domain.models import CompanyProfile

logger = logging.getLogger(__name__)


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


ACTIVE_STATES = frozenset({JobState.QUEUED, JobState.RUNNING})


@dataclass(frozen=True)
class JobStatus:
    """Immutable snapshot of a job; safe to hand to the UI thread."""

    job_id: str
    state: JobState
    message: str
    created_at: datetime


# A processor receives the validated profile and the stored file paths.
Processor = Callable[[CompanyProfile, Sequence[Path]], None]


def default_processor(profile: CompanyProfile, paths: Sequence[Path]) -> None:
    """Placeholder for the real data-processing pipeline.

    Replace the body with the actual work (parsing, analysis, calling services).
    It may raise on failure: the manager records the job as FAILED.
    """
    time.sleep(2)  # simulate work


@dataclass
class _JobRecord:
    """Internal mutable record: current status plus an event signalled on completion."""

    status: JobStatus
    done: threading.Event


class JobManager:
    """Runs processing jobs on a bounded thread pool and tracks their status."""

    def __init__(
        self,
        processor: Processor = default_processor,
        max_workers: int = 2,
        max_tracked_jobs: int = 1000,
    ) -> None:
        self._processor = processor
        # Bounded pool: protects the server from being overwhelmed by many
        # simultaneous heavy jobs; extra jobs wait in the executor's queue.
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="intake-worker")
        self._lock = threading.Lock()
        self._jobs: "OrderedDict[str, _JobRecord]" = OrderedDict()
        self._max_tracked_jobs = max_tracked_jobs

    # -- public API ---------------------------------------------------------
    def submit(self, job_id: str, profile: CompanyProfile, paths: Sequence[Path]) -> JobStatus:
        """Register a job as QUEUED, schedule it, and return its initial status."""
        status = JobStatus(job_id, JobState.QUEUED, "Waiting to start.", datetime.now(timezone.utc))
        with self._lock:
            self._jobs[job_id] = _JobRecord(status, threading.Event())
            self._evict_finished_jobs()
        self._executor.submit(self._run, job_id, profile, list(paths))
        return status

    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Return the latest status snapshot, or None for an unknown/evicted job."""
        with self._lock:
            record = self._jobs.get(job_id)
            return record.status if record else None

    def wait(self, job_id: str, timeout: Optional[float] = None) -> bool:
        """Block until the job finishes (mainly for tests). Returns False on timeout/unknown job."""
        with self._lock:
            record = self._jobs.get(job_id)
        return record.done.wait(timeout) if record else False

    def shutdown(self) -> None:
        """Stop accepting work and wait for running jobs (call on application shutdown)."""
        self._executor.shutdown(wait=True)

    # -- internals ----------------------------------------------------------
    def _run(self, job_id: str, profile: CompanyProfile, paths: list[Path]) -> None:
        """Worker body: RUNNING -> COMPLETED/FAILED, always signalling `done`.

        Exceptions are logged with a stack trace for operators, but the status
        shown to users is generic so internal details never leak to the UI.
        """
        self._set_state(job_id, JobState.RUNNING, "Processing your documents.")
        try:
            self._processor(profile, paths)
        except Exception:
            logger.exception("Job %s failed", job_id)
            self._set_state(job_id, JobState.FAILED, "Processing failed. Please try again or contact support.")
        else:
            self._set_state(job_id, JobState.COMPLETED, "Processing finished.")

    def _set_state(self, job_id: str, state: JobState, message: str) -> None:
        """Atomically replace a job's status; set the done event on terminal states."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:  # evicted while running
                return
            record.status = replace(record.status, state=state, message=message)
            if state not in ACTIVE_STATES:
                record.done.set()

    def _evict_finished_jobs(self) -> None:
        """Cap memory use: drop the oldest *finished* jobs once over the limit.

        Must be called with the lock held. Active jobs are never evicted.
        """
        if len(self._jobs) <= self._max_tracked_jobs:
            return
        for old_id in list(self._jobs):
            if len(self._jobs) <= self._max_tracked_jobs:
                break
            if self._jobs[old_id].status.state not in ACTIVE_STATES:
                del self._jobs[old_id]
