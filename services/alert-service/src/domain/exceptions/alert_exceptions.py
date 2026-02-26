"""Alert domain exceptions."""


class AlertDomainException(Exception):
    pass


class ViolationNotFoundException(AlertDomainException):
    pass


class ViolationAlreadyResolvedException(AlertDomainException):
    pass


class InvalidThresholdException(AlertDomainException):
    pass
