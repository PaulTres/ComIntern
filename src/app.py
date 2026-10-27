"""Streamlit front end: questionnaire, document upload and a "Start processing" button.

Run with:  streamlit run app.py

This file is intentionally thin. It renders widgets and displays results;
validation, persistence and job handling live in separate modules so they can be
tested and reused without Streamlit.
"""
from __future__ import annotations

import streamlit as st

import config
from logic.processing import ACTIVE_STATES, JobManager, JobState
from logic.service import submit_intake


@st.cache_resource
def get_job_manager() -> JobManager:
    """Create one JobManager per server process.

    Why cache_resource: Streamlit re-executes this script on every interaction
    and for every session. Without caching we would create a new thread pool
    (and lose all job state) each time. cache_resource keeps a single shared
    instance alive for the lifetime of the server.
    """
    return JobManager()


def render_questionnaire() -> dict:
    """Render the questionnaire widgets and return the raw answers as a dict.

    Must be called inside `st.form`. Returned values are untrusted: they are
    validated server-side in `validation.validate_profile`.
    """
    st.subheader("About your company")
    company_name = st.text_input("Company name", max_chars=config.COMPANY_NAME_MAX)
    contact_email = st.text_input(
        "Contact email", max_chars=config.EMAIL_MAX, help="We send the results and any questions here."
    )
    col_industry, col_size = st.columns(2)
    # index=None renders an empty select so users must make a deliberate choice.
    industry = col_industry.selectbox("Industry", config.INDUSTRIES, index=None, placeholder="Choose an industry")
    company_size = col_size.selectbox(
        "Number of employees", config.COMPANY_SIZES, index=None, placeholder="Choose a size"
    )
    col_country, col_site = st.columns(2)
    country = col_country.text_input("Country", max_chars=config.COUNTRY_MAX)
    website = col_site.text_input(
        "Website (optional)", max_chars=config.URL_MAX, placeholder="https://www.example.com"
    )
    primary_goal = st.text_area(
        "What do you want to achieve with this processing?",
        max_chars=config.GOAL_MAX,
        height=120,
        help="A few sentences are enough. For example: reconcile 2025 supplier contracts against our policy.",
    )
    data_sensitivity = st.radio(
        "How sensitive are the documents you are uploading?", config.DATA_SENSITIVITY, index=None, horizontal=True
    )
    return {
        "company_name": company_name,
        "contact_email": contact_email,
        "industry": industry,
        "company_size": company_size,
        "country": country,
        "website": website,
        "primary_goal": primary_goal,
        "data_sensitivity": data_sensitivity,
    }


def render_status(manager: JobManager) -> None:
    """Show the state of this session's most recent job, with a manual refresh.

    A refresh button (instead of polling) keeps the page simple and avoids
    constant server reruns; clicking it triggers a normal Streamlit rerun that
    re-reads the status.
    """
    job_id = st.session_state.get("job_id")
    if not job_id:
        return
    status = manager.get_status(job_id)
    st.divider()
    st.subheader("Processing status")
    if status is None:
        st.warning("We could not find this job. It may have expired. Submit your documents again.")
        return
    if status.state in ACTIVE_STATES:
        st.info(status.message)
    elif status.state is JobState.COMPLETED:
        st.success(status.message)
    else:
        st.error(status.message)
    st.caption(f"Reference: {status.job_id}")
    st.button("Refresh status")


def main() -> None:
    """Page entry point: build the form, handle submission, then show job status."""
    st.set_page_config(page_title=config.APP_TITLE, layout="centered")
    st.title("Tell us about your company")
    st.write("Answer a few questions, add your documents, and start processing.")

    manager = get_job_manager()

    # Disable the button while this session already has a job in flight, which
    # prevents accidental double submissions and duplicate work.
    current = manager.get_status(st.session_state.get("job_id", ""))
    busy = current is not None and current.state in ACTIVE_STATES

    # st.form batches all inputs so the script does not rerun on every keystroke
    # and the user gets all validation errors in one pass on submit.
    with st.form("intake_form"):
        raw = render_questionnaire()

        st.subheader("Your documents")
        uploads = st.file_uploader(
            f"Upload up to {config.MAX_FILES} files ({', '.join('.' + e for e in config.ALLOWED_EXTENSIONS)}), "
            f"{config.MAX_FILE_SIZE_MB} MB each",
            type=list(config.ALLOWED_EXTENSIONS),  # client-side hint only; re-checked on the server
            accept_multiple_files=True,
        )
        raw["consent"] = st.checkbox("I confirm I am allowed to share these documents for processing.")

        submitted = st.form_submit_button("Start processing", type="primary", disabled=busy)

    if submitted:
        result = submit_intake(raw, uploads or [], manager)
        if result.ok:
            st.session_state["job_id"] = result.job_id
            st.rerun()  # re-render so the button is disabled and the status panel appears
        else:
            for message in result.errors:  # messages are built from sanitised text only
                st.error(message)

    render_status(manager)


if __name__ == "__main__":
    main()
