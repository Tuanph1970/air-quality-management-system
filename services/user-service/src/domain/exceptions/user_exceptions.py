"""User domain exceptions.

All exceptions in this module inherit from ``UserDomainError`` so that
higher layers can catch the base class for generic error handling while
still distinguishing specific failure modes.
"""


class UserDomainError(Exception):
    """Base exception for all user domain errors."""

    def __init__(self, detail: str = "User domain error") -> None:
        self.detail = detail
        super().__init__(self.detail)


class UserNotFoundError(UserDomainError):
    """Raised when a user cannot be located by ID or email."""

    def __init__(self, identifier: str = "") -> None:
        detail = (
            f"User not found: {identifier}"
            if identifier
            else "User not found"
        )
        super().__init__(detail)


class UserAlreadyExistsError(UserDomainError):
    """Raised when attempting to register a user with an existing email."""

    def __init__(self, email: str = "") -> None:
        detail = (
            f"User with email '{email}' already exists"
            if email
            else "User already exists"
        )
        super().__init__(detail)


class InvalidCredentialsError(UserDomainError):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class UserInactiveError(UserDomainError):
    """Raised when attempting to authenticate an inactive user."""

    def __init__(self, email: str = "") -> None:
        detail = (
            f"User account '{email}' is inactive"
            if email
            else "User account is inactive"
        )
        super().__init__(detail)


class InvalidEmailError(UserDomainError):
    """Raised when an email format is invalid."""

    def __init__(self, email: str = "") -> None:
        detail = (
            f"Invalid email format: {email}"
            if email
            else "Invalid email format"
        )
        super().__init__(detail)


class InsufficientPermissionsError(UserDomainError):
    """Raised when a user lacks required permissions."""

    def __init__(self, required_role: str = "") -> None:
        detail = (
            f"Insufficient permissions. Required role: {required_role}"
            if required_role
            else "Insufficient permissions"
        )
        super().__init__(detail)


class PasswordTooWeakError(UserDomainError):
    """Raised when a password does not meet security requirements."""

    def __init__(self, reason: str = "") -> None:
        detail = (
            f"Password too weak: {reason}"
            if reason
            else "Password does not meet security requirements"
        )
        super().__init__(detail)
