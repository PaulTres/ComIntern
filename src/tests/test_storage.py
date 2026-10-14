"""Unit tests for persistence.py: isolation, permissions, rollback."""
import os
import stat
import uuid

import pytest

from persistence import storage

JOB = uuid.uuid4().hex


def test_saves_files_with_index_prefix_and_private_modes(tmp_path):
    paths = storage.save_documents(JOB, [("a.pdf", b"one"), ("a.pdf", memoryview(b"two"))], tmp_path)
    assert [p.name for p in paths] == ["000_a.pdf", "001_a.pdf"]  # same name, no overwrite
    assert paths[1].read_bytes() == b"two"
    if os.name == "posix":
        assert stat.S_IMODE(paths[0].stat().st_mode) == 0o600
        assert stat.S_IMODE(paths[0].parent.stat().st_mode) == 0o700


def test_hostile_filename_stays_inside_job_dir(tmp_path):
    (path,) = storage.save_documents(JOB, [("../../evil.pdf", b"x")], tmp_path)
    assert path.parent == (tmp_path / JOB).resolve()


@pytest.mark.parametrize("bad_id", ["../x", "", "abc", "A" * 32, JOB + "/.."])
def test_invalid_job_ids_rejected(tmp_path, bad_id):
    with pytest.raises(ValueError):
        storage.save_documents(bad_id, [("a.pdf", b"x")], tmp_path)


def test_existing_job_directory_is_never_reused(tmp_path):
    storage.save_documents(JOB, [("a.pdf", b"x")], tmp_path)
    with pytest.raises(FileExistsError):
        storage.save_documents(JOB, [("a.pdf", b"y")], tmp_path)


def test_failure_mid_write_removes_directory(tmp_path):
    def broken():
        yield ("a.pdf", b"ok")
        raise OSError("disk full")

    with pytest.raises(OSError):
        storage.save_documents(JOB, broken(), tmp_path)
    assert not (tmp_path / JOB).exists()


def test_delete_job_files(tmp_path):
    storage.save_documents(JOB, [("a.pdf", b"x")], tmp_path)
    storage.delete_job_files(JOB, tmp_path)
    assert not (tmp_path / JOB).exists()
    storage.delete_job_files(JOB, tmp_path)  # idempotent
