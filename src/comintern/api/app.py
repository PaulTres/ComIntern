from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from comintern.api.exception_handlers import (
    app_error_handler,
    internal_server_error_handler,
    request_validation_error_handler,
)
from comintern.api.lifespan import lifespan as default_lifespan
from comintern.api.routes import (
    auth_routes,
    chat_routes,
    company_routes,
    compliance_routes,
    document_routes,
    health_routes,
)
from comintern.configuration.config import CorsSettings
from comintern.exceptions import AppError

API_PREFIX = "/api/v1"


def create_app(
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] = default_lifespan,
    cors_settings: CorsSettings | None = None,
) -> FastAPI:
    """
    Build the application with its middleware, exception handlers and routers.

    :param lifespan: Builds the long-lived resources; tests pass their own.
    :param cors_settings: The frontend origins allowed to call the API.
    :return: The application.
    """
    app = FastAPI(title="ComIntern API", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(cors_settings or CorsSettings()).origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, internal_server_error_handler)
    for module in (
        health_routes,
        auth_routes,
        company_routes,
        compliance_routes,
        document_routes,
        chat_routes,
    ):
        app.include_router(module.router, prefix=API_PREFIX)
    return app
