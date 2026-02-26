"""Threshold checker domain service.

Stateless service that evaluates a sensor reading against an alert
configuration and determines whether a violation should be created.

This is a *domain service* because the logic spans two entities
(``AlertConfig`` and ``Violation``) and does not naturally belong to
either one.

**Domain layer rule**: this module must NOT import from the application,
infrastructure, or interface layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from ..entities.alert_config import AlertConfig
from ..entities.violation import Violation
from ..value_objects.severity import Severity


@dataclass(frozen=True)
class SensorReading:
    """Lightweight value object representing an incoming sensor reading.

    Used by the threshold checker to avoid coupling to the sensor
    service's domain.  The application layer maps the
    ``SensorReadingCreated`` event into this structure.
    """

    sensor_id: UUID
    factory_id: UUID
    pollutants: Dict[str, float]


class ThresholdChecker:
    """Checks sensor readings against configured alert thresholds.

    Usage::

        checker = ThresholdChecker()
        violation = checker.check_reading(reading, config)
        if violation:
            # persist + publish events
            ...
    """

    def check_reading(
        self,
        reading: SensorReading,
        config: AlertConfig,
    ) -> Optional[Violation]:
        """Evaluate a reading against a single alert configuration.

        Parameters
        ----------
        reading:
            The incoming sensor reading with pollutant concentrations.
        config:
            The alert configuration to check against.

        Returns
        -------
        Violation or None
            A new ``Violation`` entity if the reading exceeds the
            configured thresholds, otherwise ``None``.
        """
        if not config.is_active:
            return None

        # Get the measured value for the pollutant this config watches
        measured = reading.pollutants.get(config.pollutant)
        if measured is None:
            return None

        # Build threshold value object and check
        threshold = config.to_threshold()
        severity = threshold.check(measured)

        if severity is None:
            return None

        # Determine which threshold tier was exceeded (use warning as
        # the "permitted" value — the lowest acceptable limit)
        return Violation.create(
            factory_id=reading.factory_id,
            sensor_id=reading.sensor_id,
            pollutant=config.pollutant,
            measured_value=measured,
            permitted_value=config.warning_threshold,
            severity=severity,
        )

    def check_reading_all_configs(
        self,
        reading: SensorReading,
        configs: list[AlertConfig],
    ) -> list[Violation]:
        """Check a reading against all active configurations.

        Returns a list of violations (may be empty).
        """
        violations = []
        for config in configs:
            violation = self.check_reading(reading, config)
            if violation is not None:
                violations.append(violation)
        return violations
