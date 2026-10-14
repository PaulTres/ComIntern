"""Unit tests for logic.py: the validate -> store -> enqueue flow and its rollback."""
import config
from logic.processing import JobManager, JobState
from logic.service import submit_intake

from tests.test_validation import VALID_FORM


class FakeUpload:
    """Minimal stand-in for Streamlit's UploadedFile."""

    def __init__(self, name, data):
        self.name = name
        self._data = data

    def getbuffer(self):
        return memoryview(self._data)


PDF = FakeUpload("contract.pdf", b"%PDF-1.7 hello")


def test_success_stores_files_and_runs_job(tmp_path):
    manager = JobManager(processor=lambda p, f: None)
    result = submit_intake(VALID_FORM, [PDF], manager, tmp_path)
    assert result.ok and result.errors == []
    assert manager.wait(result.job_id, timeout=5)
    assert manager.get_status(result.job_id).state is JobState.COMPLETED
    assert [p.name for p in (tmp_path / result.job_id).iterdir()] == ["000_contract.pdf"]
    manager.shutdown()


def test_invalid_submission_writes_nothing(tmp_path):
    manager = JobManager(processor=lambda p, f: None)
    result = submit_intake({**VALID_FORM, "contact_email": "bad"}, [FakeUpload("x.exe", b"MZ")], manager, tmp_path)
    assert not result.ok and result.job_id is None
    assert len(result.errors) >= 2          # form error + file error together
    assert list(tmp_path.iterdir()) == []   # nothing stored
    manager.shutdown()


def test_missing_documents_is_an_error(tmp_path):
    manager = JobManager(processor=lambda p, f: None)
    result = submit_intake(VALID_FORM, [], manager, tmp_path)
    assert result.errors == ["Upload at least one document."]
    manager.shutdown()


def test_enqueue_failure_rolls_back_stored_files(tmp_path):
    class BrokenManager:
        def submit(self, *args):
            raise RuntimeError("queue down")

    result = submit_intake(VALID_FORM, [PDF], BrokenManager(), tmp_path)
    assert not result.ok and "could not start" in result.errors[0]
    assert list(tmp_path.iterdir()) == []


def test_storage_failure_is_reported(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")  # mkdir under a file raises OSError
    manager = JobManager(processor=lambda p, f: None)
    result = submit_intake(VALID_FORM, [PDF], manager, blocker)
    assert not result.ok and "could not store" in result.errors[0]
    manager.shutdown()


def test_only_header_bytes_are_used_for_signature_check(tmp_path):
    manager = JobManager(processor=lambda p, f: None)
    big_text = FakeUpload("big.txt", b"a" * (config.HEAD_BYTES * 3))
    assert submit_intake(VALID_FORM, [big_text], manager, tmp_path).ok
    manager.shutdown()
