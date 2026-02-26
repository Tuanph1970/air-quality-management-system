"""User domain exceptions."""


class UserDomainException(Exception):
    pass


class UserNotFoundException(UserDomainException):
    pass


class UserAlreadyExistsException(UserDomainException):
    pass


class InvalidCredentialsException(UserDomainException):
    pass


class UserInactiveException(UserDomainException):
    pass
