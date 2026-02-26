"""Factory domain exceptions.

All exceptions in this module inherit from ``FactoryDomainError`` so that
higher layers can catch the base class for generic error handling while
still distinguishing specific failure modes.
"""


class FactoryDomainError(Exception):
    """Base exception for all factory domain errors."""

    def __init__(self, detail: str = "Factory domain error") -> None:
        self.detail = detail
        super().__init__(self.detail)


class FactoryNotFoundError(FactoryDomainError):
    """Raised when a factory cannot be located by ID or registration number."""

    def __init__(self, identifier: str = "") -> None:
        detail = f"Factory not found: {identifier}" if identifier else "Factory not found"
        super().__init__(detail)


class FactoryAlreadyExistsError(FactoryDomainError):
    """Raised when attempting to create a factory with a duplicate registration number."""

    def __init__(self, registration_number: str = "") -> None:
        detail = (
            f"Factory with registration '{registration_number}' already exists"
            if registration_number
            else "Factory already exists"
        )
        super().__init__(detail)


class InvalidFactoryStatusError(FactoryDomainError):
    """Raised when a status transition violates business rules."""

    def __init__(self, current_status: str = "", target_status: str = "") -> None:
        detail = (
            f"Cannot transition from '{current_status}' to '{target_status}'"
            if current_status and target_status
            else "Invalid factory status transition"
        )
        super().__init__(detail)


class FactoryAlreadySuspendedError(FactoryDomainError):
    """Raised when trying to suspend an already-suspended factory."""

    def __init__(self) -> None:
        super().__init__("Factory is already suspended")


class FactoryNotSuspendedError(FactoryDomainError):
    """Raised when trying to resume a factory that is not suspended."""

    def __init__(self) -> None:
        super().__init__("Factory is not suspended")


class FactoryClosedError(FactoryDomainError):
    """Raised when attempting to modify a permanently closed factory."""

    def __init__(self) -> None:
        super().__init__("Factory is permanently closed and cannot be modified")
