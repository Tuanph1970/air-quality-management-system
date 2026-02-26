"""AQI prediction domain service."""


class PredictionService:
    """Predicts future AQI values."""

    def predict(self, historical_data: list, hours_ahead: int = 24) -> list:
        pass
