"""Unit tests for processing.py: lifecycle, failure handling, eviction."""
import threading

from domain.models import CompanyProfile
from logic.processing import ACTIVE_STATES, JobManager, JobState

PROFILE = CompanyProfile("Acme", "a@b.co", "Other", "1-10", "RO", "", "A goal that is long enough", "Public")


def test_job_completes_and_receives_inputs():
    seen = {}
    manager = JobManager(processor=lambda profile, paths: seen.update(profile=profile, paths=list(paths)))
    manager.submit("j1", PROFILE, ["x.pdf"])
    assert manager.wait("j1", timeout=5)
    assert manager.get_status("j1").state is JobState.COMPLETED
    assert seen["profile"] is PROFILE and seen["paths"] == ["x.pdf"]
    manager.shutdown()


def test_initial_status_is_queued_and_active_while_running():
    gate = threading.Event()
    manager = JobManager(processor=lambda p, f: gate.wait(5))
    status = manager.submit("j1", PROFILE, [])
    assert status.state is JobState.QUEUED
    assert manager.get_status("j1").state in ACTIVE_STATES
    gate.set()
    assert manager.wait("j1", timeout=5)
    manager.shutdown()


def test_processor_exception_marks_failed_without_leaking_details():
    def boom(profile, paths):
        raise RuntimeError("secret internal detail")

    manager = JobManager(processor=boom)
    manager.submit("j1", PROFILE, [])
    assert manager.wait("j1", timeout=5)
    status = manager.get_status("j1")
    assert status.state is JobState.FAILED
    assert "secret" not in status.message
    manager.shutdown()


def test_unknown_job():
    manager = JobManager()
    assert manager.get_status("nope") is None
    assert manager.wait("nope", timeout=0.01) is False
    manager.shutdown()


def test_old_finished_jobs_are_evicted_but_active_ones_are_kept():
    gate = threading.Event()
    calls = []

    def processor(profile, paths):
        calls.append(1)
        if len(calls) == 1:
            gate.wait(5)  # first job stays active

    manager = JobManager(processor=processor, max_workers=2, max_tracked_jobs=2)
    manager.submit("active", PROFILE, [])
    manager.submit("done1", PROFILE, [])
    assert manager.wait("done1", timeout=5)
    manager.submit("done2", PROFILE, [])
    assert manager.wait("done2", timeout=5)
    manager.submit("done3", PROFILE, [])
    assert manager.wait("done3", timeout=5)
    assert manager.get_status("active") is not None   # never evicted while active
    assert manager.get_status("done1") is None        # oldest finished job dropped
    gate.set()
    manager.shutdown()
