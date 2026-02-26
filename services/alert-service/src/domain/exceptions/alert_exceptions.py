"""Alert domain exceptions.

All exceptions in this module inherit from ``AlertDomainError`` so that
higher layers can catch the base class for generic error handling while
still distinguishing specific failure modes.
"""


class AlertDomainError(Exception):
    """Base exception for all alert domain errors."""

    def __init__(self, detail: str = "Alert domain error") -> None:
        self.detail = detail
        super().__init__(self.detail)


class ViolationNotFoundError(AlertDomainError):
    """Raised when a violation cannot be located by ID."""

    def __init__(self, identifier: str = "") -> None:
        detail = (
            f"Violation not found: {identifier}"
            if identifier
            else "Violation not found"
        )
        super().__init__(detail)


class ViolationAlreadyResolvedError(AlertDomainError):
    """Raised when attempting to resolve an already-resolved violation."""

    def __init__(self, identifier: str = "") -> None:
        detail = (
            f"Violation already resolved: {identifier}"
            if identifier
            else "Violation already resolved"
        )
        super().__init__(detail)


class InvalidThresholdError(AlertDomainError):
    """Raised when a threshold configuration is invalid."""

    def __init__(self, detail: str = "Invalid threshold configuration") -> None:
        super().__init__(detail)


class AlertConfigNotFoundError(AlertDomainError):
    """Raised when an alert configuration cannot be located by ID."""

    def __init__(self, identifier: str = "") -> None:
        detail = (
            f"Alert config not found: {identifier}"
            if identifier
            else "Alert config not found"
        )
        super().__init__(detail)


class DuplicateAlertConfigError(AlertDomainError):
    """Raised when creating a config for a pollutant that already has one."""

    def __init__(self, pollutant: str = "") -> None:
        detail = (
            f"Alert config for pollutant '{pollutant}' already exists"
            if pollutant
            else "Duplicate alert config"
        )
        super().__init__(detail)
