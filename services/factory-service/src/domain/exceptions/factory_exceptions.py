"""Factory domain exceptions."""


class FactoryDomainException(Exception):
    """Base factory domain exception."""
    pass


class FactoryNotFoundException(FactoryDomainException):
    pass


class FactoryAlreadyExistsException(FactoryDomainException):
    pass


class FactoryAlreadySuspendedException(FactoryDomainException):
    pass


class InvalidFactoryStatusException(FactoryDomainException):
    pass
