"""The single application error type and the catalogue of errors it can carry."""

from dataclasses import dataclass
from enum import Enum
from http import HTTPStatus
from typing import Any


@dataclass(frozen=True)
class ErrorDetail:
    """What an error code answers with."""

    status: HTTPStatus
    message: str


class AppErrorCode(Enum):
    """Every expected failure, with its HTTP status and user-safe message."""

    INTERNAL_SERVER_ERROR = ErrorDetail(
        HTTPStatus.INTERNAL_SERVER_ERROR, "Something went wrong. Please try again."
    )
    VALIDATION_ERROR = ErrorDetail(
        HTTPStatus.UNPROCESSABLE_CONTENT, "The request is invalid."
    )
    UNAUTHORIZED = ErrorDetail(HTTPStatus.UNAUTHORIZED, "Not authenticated")
    INVALID_CREDENTIALS = ErrorDetail(
        HTTPStatus.UNAUTHORIZED, "Invalid email or password"
    )
    EMAIL_ALREADY_REGISTERED = ErrorDetail(
        HTTPStatus.CONFLICT, "An account with this email already exists"
    )
    INVALID_PROFILE = ErrorDetail(
        HTTPStatus.UNPROCESSABLE_CONTENT, "Some answers are missing or invalid"
    )
    REGULATION_NOT_FOUND = ErrorDetail(
        HTTPStatus.NOT_FOUND, "Regulation not found or not applicable to your company"
    )
    REQUIREMENT_NOT_FOUND = ErrorDetail(HTTPStatus.NOT_FOUND, "Requirement not found")
    DOCUMENT_NOT_FOUND = ErrorDetail(HTTPStatus.NOT_FOUND, "Document not found")
    UNSUPPORTED_FILE_TYPE = ErrorDetail(
        HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "This file type is not supported"
    )
    FILE_TOO_LARGE = ErrorDetail(HTTPStatus.CONTENT_TOO_LARGE, "The file is too large")
    CONVERSATION_NOT_FOUND = ErrorDetail(HTTPStatus.NOT_FOUND, "Conversation not found")
    VECTOR_STORE_UNAVAILABLE = ErrorDetail(
        HTTPStatus.SERVICE_UNAVAILABLE, "The document search is unavailable right now"
    )
    CHAT_STREAM_FAILED = ErrorDetail(
        HTTPStatus.INTERNAL_SERVER_ERROR, "The assistant could not finish the answer"
    )


class AppError(Exception):
    """Raised for any expected failure that maps to an HTTP response."""

    def __init__(self, error: AppErrorCode, details: Any = None) -> None:
        """
        :param error: What went wrong.
        :param details: Replaces the code's message in the response when the caller needs
            more, e.g. the invalid questionnaire answers.
        """
        self.error = error
        self.details = details
        super().__init__(error.value.message)
