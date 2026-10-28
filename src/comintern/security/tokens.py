"""Password hashes and the access tokens a login returns."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from comintern.configuration.config import JWTSettings

password_hasher = PasswordHash.recommended()


def create_access_token(user_id: int, jwt_settings: JWTSettings) -> str:
    """
    :param user_id: The user the token signs in.
    :param jwt_settings: The signing key, algorithm and lifetime.
    :return: A signed token that expires after the configured minutes.
    """
    expires_at = datetime.now(UTC) + timedelta(minutes=jwt_settings.expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        jwt_settings.secret_key,
        jwt_settings.algorithm,
    )


def read_user_id(token: str, jwt_settings: JWTSettings) -> int | None:
    """
    :param token: The bearer token from the request.
    :param jwt_settings: The signing key and algorithm.
    :return: The user id, or None when the token is invalid, expired or malformed.
    """
    try:
        payload = jwt.decode(
            token, jwt_settings.secret_key, algorithms=[jwt_settings.algorithm]
        )
        return int(payload["sub"])
    except jwt.PyJWTError, KeyError, ValueError:
        return None
