"""Authentication and authorization exceptions.

Raised by the shared auth library and translated to HTTP responses
by the FastAPI exception handlers in each service.
"""


class AuthError(Exception):
    """Base class for all auth-related errors."""

    def __init__(self, detail: str = "Authentication error") -> None:
        self.detail = detail
        super().__init__(self.detail)


class AuthenticationError(AuthError):
    """Raised when a request cannot be authenticated.

    Typical causes:
    - Missing ``Authorization`` header
    - Malformed or expired JWT
    - Invalid signature
    """

    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(detail)


class AuthorizationError(AuthError):
    """Raised when an authenticated user lacks the required role/permission.

    The request *is* authenticated but the token's role claim does not
    satisfy the endpoint's ``require_role()`` constraint.
    """

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(detail)


class TokenExpiredError(AuthenticationError):
    """Raised specifically when a structurally valid token has expired."""

    def __init__(self) -> None:
        super().__init__("Token has expired")


class InvalidTokenError(AuthenticationError):
    """Raised when the token cannot be decoded or has an invalid signature."""

    def __init__(self, detail: str = "Invalid token") -> None:
        super().__init__(detail)
