"""Air quality domain exceptions."""


class AirQualityDomainException(Exception):
    pass


class InvalidPollutantDataException(AirQualityDomainException):
    pass


class PredictionFailedException(AirQualityDomainException):
    pass
