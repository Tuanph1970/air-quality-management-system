"""Google Maps API client."""


class GoogleMapsClient:
    """Client for Google Maps API integration."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def geocode(self, address: str) -> dict:
        pass

    async def reverse_geocode(self, lat: float, lng: float) -> dict:
        pass
