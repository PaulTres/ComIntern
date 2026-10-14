"""Smoke tests for the Streamlit page using Streamlit's AppTest harness.

AppTest cannot simulate file uploads, so these tests cover rendering and the
validation-failure path; the full success path is covered in test_service.py.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_page_renders_questionnaire_and_submit_button():
    at = AppTest.from_file(APP, default_timeout=15).run()
    assert not at.exception
    assert at.title[0].value == "Tell us about your company"
    labels = [t.label for t in at.text_input]
    assert "Company name" in labels and "Contact email" in labels
    assert len(at.selectbox) == 2
    assert at.button[0].label == "Start processing"


def test_submitting_empty_form_shows_errors_and_no_job():
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.error) >= 5
    assert "job_id" not in at.session_state
