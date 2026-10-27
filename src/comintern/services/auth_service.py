from comintern.configuration.config import JWTSettings
from comintern.database.session_factory import SessionFactory
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.auth import (
    LoginRequestModel,
    RegisterRequestModel,
    TokenResponseModel,
    UserResponseModel,
)
from comintern.repositories.user_repository import UserRepository
from comintern.schemas import Company, User
from comintern.security.tokens import create_access_token, password_hasher


class AuthService:
    """Sign-up, login and finding the user behind a token."""

    def __init__(
        self, session_factory: SessionFactory, jwt_settings: JWTSettings
    ) -> None:
        self._session_factory = session_factory
        self._jwt_settings = jwt_settings

    async def register(self, request: RegisterRequestModel) -> TokenResponseModel:
        """
        Create the company and its first user, and sign them in.

        :raises AppError: EMAIL_ALREADY_REGISTERED when the email is taken.
        """
        email = request.email.lower()
        async with self._session_factory.get_session() as session:
            users = UserRepository(session)
            if await users.get_by_email(email):
                raise AppError(AppErrorCode.EMAIL_ALREADY_REGISTERED)
            user = User(
                email=email,
                password_hash=password_hasher.hash(request.password),
                company=Company(name=request.company_name),
            )
            await users.add(user)
            return self._token_response(user)

    async def login(self, request: LoginRequestModel) -> TokenResponseModel:
        """
        :raises AppError: INVALID_CREDENTIALS for an unknown email or a wrong password.
        """
        async with self._session_factory.get_session() as session:
            user = await UserRepository(session).get_by_email(request.email.lower())
            if user is None or not password_hasher.verify(
                request.password, user.password_hash
            ):
                raise AppError(AppErrorCode.INVALID_CREDENTIALS)
            return self._token_response(user)

    async def get_user(self, user_id: int) -> User | None:
        """
        :return: The user with their company loaded, or None when the account is gone.
        """
        async with self._session_factory.get_session() as session:
            return await UserRepository(session).get(user_id)

    def _token_response(self, user: User) -> TokenResponseModel:
        return TokenResponseModel(
            access_token=create_access_token(user.id, self._jwt_settings),
            user=UserResponseModel.model_validate(user),
        )
