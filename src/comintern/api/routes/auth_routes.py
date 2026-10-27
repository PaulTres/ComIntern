from http import HTTPStatus

from fastapi import APIRouter

from comintern.api.dependencies import AuthServiceDependency, CurrentUserDependency
from comintern.models.auth import (
    LoginRequestModel,
    RegisterRequestModel,
    TokenResponseModel,
    UserResponseModel,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenResponseModel, status_code=HTTPStatus.CREATED
)
async def register(
    body: RegisterRequestModel, auth_service: AuthServiceDependency
) -> TokenResponseModel:
    """Create a company and its first user, and sign them in."""
    return await auth_service.register(body)


@router.post("/login", response_model=TokenResponseModel)
async def login(
    body: LoginRequestModel, auth_service: AuthServiceDependency
) -> TokenResponseModel:
    return await auth_service.login(body)


@router.get("/me", response_model=UserResponseModel)
async def get_me(user: CurrentUserDependency) -> UserResponseModel:
    return UserResponseModel.model_validate(user)
