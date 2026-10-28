"""Request-scoped providers: the services built in the lifespan, and the signed-in user."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from comintern.exceptions import AppError, AppErrorCode
from comintern.models.chat import ChatStreamRequestModel
from comintern.models.stream import StreamEventModel
from comintern.schemas import User
from comintern.security.tokens import read_user_id
from comintern.services.auth_service import AuthService
from comintern.services.chat_service import ChatService
from comintern.services.company_service import CompanyService
from comintern.services.compliance_service import ComplianceService
from comintern.services.document_service import DocumentService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_company_service(request: Request) -> CompanyService:
    return request.app.state.company_service


def get_compliance_service(request: Request) -> ComplianceService:
    return request.app.state.compliance_service


def get_document_service(request: Request) -> DocumentService:
    return request.app.state.document_service


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
CompanyServiceDependency = Annotated[CompanyService, Depends(get_company_service)]
ComplianceServiceDependency = Annotated[
    ComplianceService, Depends(get_compliance_service)
]
DocumentServiceDependency = Annotated[DocumentService, Depends(get_document_service)]
ChatServiceDependency = Annotated[ChatService, Depends(get_chat_service)]


async def get_current_user(
    request: Request,
    auth_service: AuthServiceDependency,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """
    :return: The user the bearer token signs in, with their company.
    :raises AppError: UNAUTHORIZED when the token is missing, invalid, expired, or the user is gone.
    """
    user_id = (
        read_user_id(credentials.credentials, request.app.state.settings.jwt)
        if credentials
        else None
    )
    user = await auth_service.get_user(user_id) if user_id is not None else None
    if user is None:
        raise AppError(AppErrorCode.UNAUTHORIZED)
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


async def get_chat_stream(
    body: ChatStreamRequestModel,
    user: CurrentUserDependency,
    chat_service: ChatServiceDependency,
) -> AsyncGenerator[AsyncGenerator[StreamEventModel]]:
    """
    Prepare the turn before the response starts, and close the stream when the request ends,
    also when the client disconnects.
    """
    stream = await chat_service.prepare_turn(user, body)
    try:
        yield stream
    finally:
        await stream.aclose()


ChatStreamDependency = Annotated[
    AsyncGenerator[StreamEventModel], Depends(get_chat_stream)
]
