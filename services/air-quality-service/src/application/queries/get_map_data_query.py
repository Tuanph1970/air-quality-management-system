"""Query to get aggregated AQI data for map visualization."""
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID


@dataclass
class GetMapDataQuery:
    """Query to get AQI data for map visualization.

    Attributes
    ----------
    bounds:
        Map bounding box (min_lat, min_lng, max_lat, max_lng)
    zoom_level:
        Current map zoom level (determines grid size)
    grid_size:
        Size of grid cells in degrees (calculated from zoom)
    include_forecast:
        Whether to include forecast data
    """

    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float
    zoom_level: int = 10
    grid_size: Optional[float] = None
    include_forecast: bool = False

    def __post_init__(self):
        """Calculate grid size from zoom level if not provided."""
        if self.grid_size is None:
            # Approximate grid size based on zoom level
            # Higher zoom = smaller grid cells
            self.grid_size = 360.0 / (2 ** (self.zoom_level + 4))


@dataclass
class MapGridCell:
    """A single grid cell for map visualization.

    Attributes
    ----------
    lat:
        Center latitude of the cell
    lng:
        Center longitude of the cell
    aqi_value:
        Average AQI for the cell
    level:
        AQI level for the cell
    color:
        Color code for display
    sensor_count:
        Number of sensors contributing data
    last_updated:
        Timestamp of most recent reading
    """

    lat: float
    lng: float
    aqi_value: int
    level: str
    color: str
    sensor_count: int = 0
    last_updated: str = ""
    forecast_aqi: Optional[int] = None


@dataclass
class GetMapDataResult:
    """Result of map data query.

    Attributes
    ----------
    grid_cells:
        List of grid cells with AQI data
    bounds:
        The queried bounding box
    zoom_level:
        The zoom level used
    generated_at:
        When the data was generated
    """

    grid_cells: List[MapGridCell] = field(default_factory=list)
    min_lat: float = 0.0
    min_lng: float = 0.0
    max_lat: float = 0.0
    max_lng: float = 0.0
    zoom_level: int = 0
    generated_at: str = ""
