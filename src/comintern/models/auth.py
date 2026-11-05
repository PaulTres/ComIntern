"""Sign-up, login and the signed-in user."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequestModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    company_name: str = Field(min_length=1, max_length=255)


class LoginRequestModel(BaseModel):
    email: EmailStr
    password: str


class CompanyResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    profile: dict[str, Any] | None
    assessed_at: datetime | None


class CompanyUpdateRequestModel(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    profile: dict[str, Any] | None = None


class UserResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    company: CompanyResponseModel


class TokenResponseModel(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponseModel
