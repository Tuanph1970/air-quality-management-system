"""Pydantic schemas for User Service API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# =============================================================================
# Authentication Schemas
# =============================================================================


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role: str = Field(default="PUBLIC", description="User role")
    organization: Optional[str] = Field(None, max_length=255, description="Organization")

    model_config = {"json_schema_extra": {"example": {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe",
        "role": "PUBLIC",
        "organization": None,
    }}}


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")

    model_config = {"json_schema_extra": {"example": {
        "email": "user@example.com",
        "password": "SecurePass123!",
    }}}


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


# =============================================================================
# User Schemas
# =============================================================================


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role")
    organization: Optional[str] = Field(None, description="Organization")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response schema for JWT token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token expiration in seconds")
    user: Optional[UserResponse] = Field(None, description="User information")


class UpdateProfileRequest(BaseModel):
    """Request schema for profile update."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization: Optional[str] = Field(None, max_length=255)


class ChangePasswordRequest(BaseModel):
    """Request schema for password change."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""

    email: EmailStr = Field(..., description="Email address of the account")


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset."""

    token: str = Field(..., description="Password reset token received via email")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password."""

    message: str = Field(..., description="Status message")
    reset_token: Optional[str] = Field(None, description="Reset token (development only – omitted in production)")
