"""Sensor domain exceptions."""


class SensorDomainException(Exception):
    pass


class SensorNotFoundException(SensorDomainException):
    pass


class InvalidReadingException(SensorDomainException):
    pass


class SensorNotCalibratedExcep(SensorDomainException):
    pass
