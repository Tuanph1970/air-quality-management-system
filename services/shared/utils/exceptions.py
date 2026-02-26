"""Shared exception definitions."""


class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found."""
    pass


class ValidationException(DomainException):
    """Raised when validation fails."""
    pass


class AuthenticationException(DomainException):
    """Raised when authentication fails."""
    pass


class AuthorizationException(DomainException):
    """Raised when authorization fails."""
    pass
