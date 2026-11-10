"""Validate authentication requests and expose safe account/token data."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

UserRole = Literal["superadmin", "admin", "user"]


class RegisterRequest(BaseModel):
    """Credentials accepted for public account registration."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Normalize email addresses for consistent uniqueness checks."""
        return str(value).strip().lower()


class LoginRequest(BaseModel):
    """Email and password submitted to the login endpoint."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Normalize email addresses before account lookup."""
        return str(value).strip().lower()


class UserResponse(BaseModel):
    """Public user details that intentionally omit credential fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole


class AccessTokenResponse(BaseModel):
    """Bearer access token returned after successful login."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse
