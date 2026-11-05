"""Turn application errors and unexpected failures into the one error body: {"code", "detail"}.

`detail` is the user-safe message, or the extra details an error carries (e.g. the invalid
questionnaire answers), so the frontend reads `detail` as it always did.
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from comintern.exceptions import AppError, AppErrorCode

logger = logging.getLogger(__name__)


def build_error_response(
    error_code: AppErrorCode, details: object = None
) -> JSONResponse:
    return JSONResponse(
        status_code=error_code.value.status,
        content={
            "code": error_code.name,
            "detail": details if details is not None else error_code.value.message,
        },
    )


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    return build_error_response(error.error, error.details)


async def request_validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    """The log gets where each problem is and its type, never the rejected input."""
    logger.info(
        "Invalid request method=%s path=%s problems=%s",
        request.method,
        request.url.path,
        [(problem["loc"], problem["type"]) for problem in error.errors()],
    )
    return build_error_response(
        AppErrorCode.VALIDATION_ERROR,
        [{"loc": problem["loc"], "msg": problem["msg"]} for problem in error.errors()],
    )


async def internal_server_error_handler(
    request: Request, error: Exception
) -> JSONResponse:
    """The details go to the log, never to the client."""
    logger.exception(
        "Unhandled error method=%s path=%s", request.method, request.url.path
    )
    return build_error_response(AppErrorCode.INTERNAL_SERVER_ERROR)
