"""Central configuration for the company intake application.

Why a dedicated module: limits, allowed values and paths are referenced by the
UI (to render options and hints), by validation (to enforce them server-side)
and by tests. Keeping a single source of truth prevents the UI and the
validation rules from drifting apart.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

APP_TITLE = "Company onboarding"

# --- Upload limits -----------------------------------------------------------
# Enforced server-side in validation.py. The file_uploader `type=` filter and
# Streamlit's maxUploadSize are only client/transport-level conveniences.
MAX_FILES = 10
MAX_FILE_SIZE_MB = 25          # keep <= server.maxUploadSize in .streamlit/config.toml
MAX_TOTAL_SIZE_MB = 100
ALLOWED_EXTENSIONS = ("pdf", "docx", "xlsx", "csv", "txt")
# Number of leading bytes inspected to confirm a file's content matches its extension.
HEAD_BYTES = 2048

# --- Questionnaire options ---------------------------------------------------
# Selects are validated against these tuples so a tampered request cannot
# smuggle in arbitrary values.
INDUSTRIES = (
    "Software & technology",
    "Financial services",
    "Healthcare & life sciences",
    "Manufacturing",
    "Retail & e-commerce",
    "Professional services",
    "Education",
    "Public sector & non-profit",
    "Other",
)
COMPANY_SIZES = ("1-10", "11-50", "51-200", "201-1,000", "1,000+")
DATA_SENSITIVITY = ("Public", "Internal", "Confidential", "Highly confidential")

# --- Field length limits -----------------------------------------------------
COMPANY_NAME_MIN, COMPANY_NAME_MAX = 2, 120
COUNTRY_MIN, COUNTRY_MAX = 2, 80
GOAL_MIN, GOAL_MAX = 10, 2000
EMAIL_MAX = 254   # RFC 5321 limit
URL_MAX = 2048


def get_upload_root() -> Path:
    """Return the directory under which per-job upload folders are created.

    Overridable through the INTAKE_UPLOAD_DIR environment variable so
    deployments can point to a dedicated, encrypted volume. The default lives
    in the system temp dir, which is fine for development only.
    """
    configured = os.environ.get("INTAKE_UPLOAD_DIR")
    return Path(configured) if configured else Path(tempfile.gettempdir()) / "company_intake_uploads"
