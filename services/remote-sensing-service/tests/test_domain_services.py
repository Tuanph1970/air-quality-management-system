"""Tests for Remote Sensing Service domain layer.

Tests cover:
- Satellite Data entity
- Excel Import entity
- Value objects (GeoPolygon, SatelliteSource, QualityFlag)
- Satellite data service
- Excel import service
- Data parsers
"""
import pytest
from datetime import datetime, date
from uuid import uuid4, UUID
import io

from src.domain.entities.satellite_data import SatelliteData
from src.domain.entities.excel_import import ExcelImport, ImportStatus
from src.domain.value_objects.geo_polygon import GeoPolygon
from src.domain.value_objects.satellite_source import SatelliteSource
from src.domain.value_objects.quality_flag import QualityFlag
from src.domain.services.data_processor import DataProcessor


# =============================================================================
# Value Object Tests
# =============================================================================

class TestGeoPolygon:
    """Test GeoPolygon value object."""

    def test_create_valid_polygon(self):
        """Test creating a valid GeoPolygon."""
        polygon = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        assert polygon.north == 11.0
        assert polygon.south == 10.0
        assert polygon.east == 107.0
        assert polygon.west == 106.0

    def test_contains_point(self):
        """Test point containment check."""
        polygon = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        # Point inside
        assert polygon.contains(10.5, 106.5) is True
        
        # Point outside (north)
        assert polygon.contains(11.5, 106.5) is False
        
        # Point outside (south)
        assert polygon.contains(9.5, 106.5) is False
        
        # Point outside (east)
        assert polygon.contains(10.5, 107.5) is False
        
        # Point outside (west)
        assert polygon.contains(10.5, 105.5) is False

    def test_get_center(self):
        """Test center point calculation."""
        polygon = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        center = polygon.get_center()
        
        assert center == (10.5, 106.5)

    def test_area_calculation(self):
        """Test area calculation."""
        polygon = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        area = polygon.area()
        
        assert area > 0
        assert isinstance(area, float)

    def test_invalid_polygon(self):
        """Test that invalid polygons raise errors."""
        # North should be greater than south
        with pytest.raises(ValueError):
            GeoPolygon(
                north=10.0,
                south=11.0,
                east=107.0,
                west=106.0,
            )


class TestSatelliteSource:
    """Test SatelliteSource value object."""

    def test_source_values(self):
        """Test satellite source enum values."""
        assert SatelliteSource.CAMS_PM25.value == "cams_pm25"
        assert SatelliteSource.CAMS_PM10.value == "cams_pm10"
        assert SatelliteSource.CAMS_FORECAST.value == "cams_forecast"
        assert SatelliteSource.MODIS_TERRA.value == "modis_terra"
        assert SatelliteSource.MODIS_AQUA.value == "modis_aqua"
        assert SatelliteSource.TROPOMI_NO2.value == "tropomi_no2"
        assert SatelliteSource.TROPOMI_SO2.value == "tropomi_so2"

    def test_source_from_string(self):
        """Test creating source from string value."""
        source = SatelliteSource("cams_pm25")
        assert source == SatelliteSource.CAMS_PM25

    def test_invalid_source(self):
        """Test that invalid source raises error."""
        with pytest.raises(ValueError):
            SatelliteSource("invalid_source")


class TestQualityFlag:
    """Test QualityFlag value object."""

    def test_quality_flag_values(self):
        """Test quality flag enum values."""
        assert QualityFlag.GOOD.value == "good"
        assert QualityFlag.MEDIUM.value == "medium"
        assert QualityFlag.LOW.value == "low"
        assert QualityFlag.INVALID.value == "invalid"


# =============================================================================
# Entity Tests
# =============================================================================

class TestSatelliteData:
    """Test SatelliteData entity."""

    def test_create_satellite_data(self):
        """Test creating a SatelliteData entity."""
        bbox = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        grid_cells = [
            {"lat": 10.5, "lon": 106.5, "value": 0.5, "uncertainty": 0.1},
            {"lat": 10.6, "lon": 106.6, "value": 0.6, "uncertainty": 0.1},
        ]
        
        data = SatelliteData.create(
            source=SatelliteSource.CAMS_PM25,
            data_type="PM25",
            observation_time=datetime.utcnow(),
            bbox=bbox,
            grid_cells=grid_cells,
            quality_flag=QualityFlag.GOOD,
            metadata={"test": "value"},
        )
        
        assert isinstance(data.id, UUID)
        assert data.source == SatelliteSource.CAMS_PM25
        assert data.data_type == "PM25"
        assert len(data.grid_cells) == 2
        assert data.quality_flag == QualityFlag.GOOD

    def test_get_value_at_location(self):
        """Test getting satellite value at a location."""
        bbox = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        grid_cells = [
            {"lat": 10.5, "lon": 106.5, "value": 0.5, "uncertainty": 0.1},
            {"lat": 10.6, "lon": 106.6, "value": 0.6, "uncertainty": 0.1},
        ]
        
        data = SatelliteData.create(
            source=SatelliteSource.CAMS_PM25,
            data_type="PM25",
            observation_time=datetime.utcnow(),
            bbox=bbox,
            grid_cells=grid_cells,
            quality_flag=QualityFlag.GOOD,
        )
        
        value = data.get_value_at_location(10.5, 106.5)
        assert value is not None
        assert value["value"] == 0.5

    def test_to_dict(self):
        """Test serialization to dictionary."""
        bbox = GeoPolygon(
            north=11.0,
            south=10.0,
            east=107.0,
            west=106.0,
        )
        
        data = SatelliteData.create(
            source=SatelliteSource.CAMS_PM25,
            data_type="PM25",
            observation_time=datetime.utcnow(),
            bbox=bbox,
            grid_cells=[{"lat": 10.5, "lon": 106.5, "value": 0.5}],
            quality_flag=QualityFlag.GOOD,
        )
        
        data_dict = data.to_dict()
        
        assert isinstance(data_dict, dict)
        assert data_dict["source"] == "cams_pm25"
        assert data_dict["data_type"] == "PM25"
        assert "id" in data_dict
        assert "observation_time" in data_dict


class TestExcelImport:
    """Test ExcelImport entity."""

    def test_create_excel_import(self):
        """Test creating an ExcelImport entity."""
        excel_import = ExcelImport.create(
            filename="test_data.xlsx",
            data_type="historical_readings",
            record_count=100,
        )
        
        assert isinstance(excel_import.id, UUID)
        assert excel_import.filename == "test_data.xlsx"
        assert excel_import.data_type == "historical_readings"
        assert excel_import.record_count == 100
        assert excel_import.status == ImportStatus.PENDING

    def test_mark_completed(self):
        """Test marking import as completed."""
        excel_import = ExcelImport.create(
            filename="test_data.xlsx",
            data_type="historical_readings",
            record_count=100,
        )
        
        excel_import.mark_completed(processed_count=95, error_count=5)
        
        assert excel_import.status == ImportStatus.COMPLETED
        assert excel_import.processed_count == 95
        assert excel_import.error_count == 5

    def test_mark_failed(self):
        """Test marking import as failed."""
        excel_import = ExcelImport.create(
            filename="test_data.xlsx",
            data_type="historical_readings",
            record_count=100,
        )
        
        excel_import.mark_failed(errors=["Invalid format", "Missing columns"])
        
        assert excel_import.status == ImportStatus.FAILED
        assert len(excel_import.errors) == 2


# =============================================================================
# Domain Service Tests
# =============================================================================

class TestDataProcessor:
    """Test data processing domain service."""

    @pytest.fixture
    def processor(self):
        return DataProcessor()

    def test_validate_coordinates(self, processor):
        """Test coordinate validation."""
        assert processor.validate_coordinates(10.5, 106.5) is True
        assert processor.validate_coordinates(91.0, 106.5) is False  # Invalid lat
        assert processor.validate_coordinates(10.5, 181.0) is False  # Invalid lon

    def test_interpolate_grid(self, processor):
        """Test grid interpolation."""
        grid_points = [
            {"lat": 10.0, "lon": 106.0, "value": 100},
            {"lat": 10.0, "lon": 107.0, "value": 200},
            {"lat": 11.0, "lon": 106.0, "value": 150},
            {"lat": 11.0, "lon": 107.0, "value": 250},
        ]
        
        interpolated = processor.interpolate_grid(
            grid_points=grid_points,
            target_lat=10.5,
            target_lon=106.5,
        )
        
        assert interpolated is not None
        assert 100 <= interpolated <= 250

    def test_calculate_statistics(self, processor):
        """Test statistical calculations."""
        values = [10, 20, 30, 40, 50]
        
        stats = processor.calculate_statistics(values)
        
        assert stats["mean"] == 30.0
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["count"] == 5


# =============================================================================
# Integration Tests
# =============================================================================

class TestSatelliteDataIntegration:
    """Integration tests for satellite data workflow."""

    def test_full_workflow(self):
        """Test complete satellite data workflow."""
        # Create bounding box for Ho Chi Minh City
        bbox = GeoPolygon(
            north=11.2,
            south=10.3,
            east=107.1,
            west=106.3,
        )
        
        # Create satellite data
        grid_cells = [
            {"lat": 10.5, "lon": 106.5, "value": 0.5, "uncertainty": 0.1},
            {"lat": 10.8, "lon": 106.8, "value": 0.6, "uncertainty": 0.1},
            {"lat": 11.0, "lon": 107.0, "value": 0.4, "uncertainty": 0.1},
        ]
        
        data = SatelliteData.create(
            source=SatelliteSource.CAMS_PM25,
            data_type="PM25",
            observation_time=datetime.utcnow(),
            bbox=bbox,
            grid_cells=grid_cells,
            quality_flag=QualityFlag.GOOD,
            metadata={"forecast_hours": 24},
        )
        
        # Verify data
        assert data.source == SatelliteSource.CAMS_PM25
        assert len(data.grid_cells) == 3
        
        # Get value at specific location
        value = data.get_value_at_location(10.5, 106.5)
        assert value is not None
        assert value["value"] == 0.5
        
        # Serialize
        data_dict = data.to_dict()
        assert data_dict["source"] == "cams_pm25"
        assert data_dict["grid_cell_count"] == 3
        
        # Check bbox containment
        assert bbox.contains(10.5, 106.5) is True
        assert bbox.contains(15.0, 106.5) is False
