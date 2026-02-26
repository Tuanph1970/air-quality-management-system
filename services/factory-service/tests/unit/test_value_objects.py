"""Unit tests for factory domain value objects."""
from __future__ import annotations

import pytest

from src.domain.value_objects.emission_limit import EmissionLimits
from src.domain.value_objects.factory_status import FactoryStatus
from src.domain.value_objects.location import Location


# =========================================================================
# Location
# =========================================================================
class TestLocation:
    def test_create_valid_location(self):
        loc = Location(latitude=21.0285, longitude=105.8542)
        assert loc.latitude == 21.0285
        assert loc.longitude == 105.8542

    def test_boundary_values(self):
        loc1 = Location(latitude=-90.0, longitude=-180.0)
        assert loc1.latitude == -90.0
        loc2 = Location(latitude=90.0, longitude=180.0)
        assert loc2.latitude == 90.0

    def test_invalid_latitude_above(self):
        with pytest.raises(ValueError, match="Latitude"):
            Location(latitude=91.0, longitude=0.0)

    def test_invalid_latitude_below(self):
        with pytest.raises(ValueError, match="Latitude"):
            Location(latitude=-91.0, longitude=0.0)

    def test_invalid_longitude_above(self):
        with pytest.raises(ValueError, match="Longitude"):
            Location(latitude=0.0, longitude=181.0)

    def test_invalid_longitude_below(self):
        with pytest.raises(ValueError, match="Longitude"):
            Location(latitude=0.0, longitude=-181.0)

    def test_immutable(self):
        loc = Location(latitude=10.0, longitude=20.0)
        with pytest.raises(AttributeError):
            loc.latitude = 30.0

    def test_distance_to_same_point_is_zero(self):
        loc = Location(latitude=21.0, longitude=105.0)
        assert loc.distance_to(loc) == pytest.approx(0.0, abs=0.01)

    def test_distance_to_known_points(self):
        hanoi = Location(latitude=21.0285, longitude=105.8542)
        hcmc = Location(latitude=10.8231, longitude=106.6297)
        dist = hanoi.distance_to(hcmc)
        assert 1130 < dist < 1150  # ~1,140 km

    def test_equality(self):
        a = Location(latitude=10.0, longitude=20.0)
        b = Location(latitude=10.0, longitude=20.0)
        assert a == b

    def test_inequality(self):
        a = Location(latitude=10.0, longitude=20.0)
        b = Location(latitude=10.0, longitude=21.0)
        assert a != b


# =========================================================================
# EmissionLimits
# =========================================================================
class TestEmissionLimits:
    def test_create_defaults(self):
        el = EmissionLimits()
        assert el.pm25_limit == 0.0
        assert el.o3_limit == 0.0

    def test_create_from_dict(self):
        el = EmissionLimits.from_dict({
            "pm25_limit": 50.0,
            "pm10_limit": 100.0,
            "co_limit": 10.0,
        })
        assert el.pm25_limit == 50.0
        assert el.pm10_limit == 100.0
        assert el.co_limit == 10.0
        assert el.no2_limit == 0.0  # not provided, defaults to 0

    def test_from_dict_ignores_unknown_keys(self):
        el = EmissionLimits.from_dict({"pm25_limit": 50.0, "unknown_key": 999.0})
        assert el.pm25_limit == 50.0

    def test_to_dict(self):
        el = EmissionLimits(pm25_limit=50.0, pm10_limit=100.0)
        d = el.to_dict()
        assert d["pm25_limit"] == 50.0
        assert d["pm10_limit"] == 100.0
        assert len(d) == 6  # all 6 pollutants

    def test_roundtrip_dict(self, sample_emission_limits):
        el = EmissionLimits.from_dict(sample_emission_limits)
        assert el.to_dict() == sample_emission_limits

    def test_immutable(self):
        el = EmissionLimits(pm25_limit=50.0)
        with pytest.raises(AttributeError):
            el.pm25_limit = 60.0

    def test_negative_value_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            EmissionLimits(pm25_limit=-1.0)

    def test_is_exceeded_true(self):
        el = EmissionLimits(pm25_limit=50.0, pm10_limit=100.0)
        assert el.is_exceeded({"pm25": 55.0}) is True

    def test_is_exceeded_false(self):
        el = EmissionLimits(pm25_limit=50.0, pm10_limit=100.0)
        assert el.is_exceeded({"pm25": 45.0, "pm10": 90.0}) is False

    def test_is_exceeded_zero_limit_ignored(self):
        el = EmissionLimits(pm25_limit=0.0)
        assert el.is_exceeded({"pm25": 100.0}) is False

    def test_exceeded_pollutants(self):
        el = EmissionLimits(pm25_limit=50.0, pm10_limit=100.0, co_limit=10.0)
        breaches = el.exceeded_pollutants({"pm25": 55.0, "pm10": 90.0, "co": 15.0})
        assert "pm25" in breaches
        assert "co" in breaches
        assert "pm10" not in breaches
        assert breaches["pm25"]["measured"] == 55.0
        assert breaches["pm25"]["limit"] == 50.0

    def test_exceeded_pollutants_empty_when_safe(self):
        el = EmissionLimits(pm25_limit=50.0)
        assert el.exceeded_pollutants({"pm25": 30.0}) == {}


# =========================================================================
# FactoryStatus
# =========================================================================
class TestFactoryStatus:
    def test_all_values_exist(self):
        assert FactoryStatus.ACTIVE.value == "ACTIVE"
        assert FactoryStatus.WARNING.value == "WARNING"
        assert FactoryStatus.CRITICAL.value == "CRITICAL"
        assert FactoryStatus.SUSPENDED.value == "SUSPENDED"
        assert FactoryStatus.CLOSED.value == "CLOSED"

    def test_is_operational_active(self):
        assert FactoryStatus.ACTIVE.is_operational is True

    def test_is_operational_warning(self):
        assert FactoryStatus.WARNING.is_operational is True

    def test_is_operational_critical(self):
        assert FactoryStatus.CRITICAL.is_operational is True

    def test_is_operational_suspended(self):
        assert FactoryStatus.SUSPENDED.is_operational is False

    def test_is_operational_closed(self):
        assert FactoryStatus.CLOSED.is_operational is False

    def test_is_terminal_closed(self):
        assert FactoryStatus.CLOSED.is_terminal is True

    def test_is_terminal_active(self):
        assert FactoryStatus.ACTIVE.is_terminal is False

    def test_is_terminal_suspended(self):
        assert FactoryStatus.SUSPENDED.is_terminal is False

    def test_string_enum(self):
        assert str(FactoryStatus.ACTIVE) == "FactoryStatus.ACTIVE"
        assert FactoryStatus("ACTIVE") == FactoryStatus.ACTIVE
