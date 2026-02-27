"""Unit tests for AlertApplicationService."""
import pytest
from uuid import uuid4

from src.application.services.alert_application_service import AlertApplicationService
from src.application.commands.resolve_violation_command import ResolveViolationCommand
from src.application.queries.get_violations_query import GetViolationsQuery
from src.domain.exceptions.alert_exceptions import ViolationNotFoundError


class TestAlertServiceProcessReading:
    """Tests for AlertApplicationService.process_reading() method."""

    @pytest.mark.anyio
    async def test_process_reading_no_configs(
        self, alert_service, mock_publisher, sample_sensor_id, sample_factory_id
    ):
        """Test processing a reading when no alert configs exist."""
        violations = await alert_service.process_reading(
            sensor_id=sample_sensor_id,
            factory_id=sample_factory_id,
            pollutants={"pm25": 85.0},
        )

        assert len(violations) == 0
        assert len(mock_publisher.events) == 0

    @pytest.mark.anyio
    async def test_process_reading_below_threshold(
        self, alert_service, mock_publisher, sample_sensor_id, sample_factory_id,
        in_memory_alert_config_repo
    ):
        """Test processing a reading below threshold."""
        from src.domain.entities.alert_config import AlertConfig

        # Create a config with high threshold
        config = AlertConfig.create(
            name="PM2.5 Limit",
            pollutant="pm25",
            warning_threshold=35.0,
            high_threshold=55.0,
            critical_threshold=150.0,
        )
        await in_memory_alert_config_repo.save(config)

        violations = await alert_service.process_reading(
            sensor_id=sample_sensor_id,
            factory_id=sample_factory_id,
            pollutants={"pm25": 10.0},  # Below threshold
        )

        assert len(violations) == 0

    @pytest.mark.anyio
    async def test_process_reading_creates_violation(
        self, alert_service, mock_publisher, sample_sensor_id, sample_factory_id,
        in_memory_alert_config_repo
    ):
        """Test that exceeding threshold creates a violation."""
        from src.domain.entities.alert_config import AlertConfig

        config = AlertConfig.create(
            name="PM2.5 Limit",
            pollutant="pm25",
            warning_threshold=35.0,
            high_threshold=55.0,
            critical_threshold=150.0,
        )
        await in_memory_alert_config_repo.save(config)

        violations = await alert_service.process_reading(
            sensor_id=sample_sensor_id,
            factory_id=sample_factory_id,
            pollutants={"pm25": 85.0},  # Exceeds warning threshold
        )

        assert len(violations) > 0
        assert violations[0].pollutant == "pm25"
        assert violations[0].factory_id == sample_factory_id
        assert violations[0].sensor_id == sample_sensor_id


class TestAlertServiceCreateViolation:
    """Tests for AlertApplicationService.create_violation() method."""

    @pytest.mark.anyio
    async def test_create_violation_success(
        self, alert_service, mock_publisher, sample_factory_id, sample_sensor_id
    ):
        """Test creating a violation manually."""
        from src.application.commands.create_violation_command import CreateViolationCommand

        command = CreateViolationCommand(
            factory_id=sample_factory_id,
            sensor_id=sample_sensor_id,
            pollutant="pm25",
            measured_value=100.0,
            permitted_value=50.0,
            severity="HIGH",
        )

        violation = await alert_service.create_violation(command)

        assert violation is not None
        assert violation.pollutant == "pm25"
        assert violation.measured_value == 100.0
        assert len(mock_publisher.events) > 0

    @pytest.mark.anyio
    async def test_create_violation_publishes_event(
        self, alert_service, mock_publisher, sample_factory_id, sample_sensor_id
    ):
        """Test that creating a violation publishes an event."""
        from src.application.commands.create_violation_command import CreateViolationCommand
        from shared.events.alert_events import ViolationDetected

        command = CreateViolationCommand(
            factory_id=sample_factory_id,
            sensor_id=sample_sensor_id,
            pollutant="co",
            measured_value=25.0,
            permitted_value=10.0,
            severity="CRITICAL",
        )

        await alert_service.create_violation(command)

        assert len(mock_publisher.events) == 1
        assert isinstance(mock_publisher.events[0], ViolationDetected)


class TestAlertServiceResolveViolation:
    """Tests for AlertApplicationService.resolve_violation() method."""

    @pytest.mark.anyio
    async def test_resolve_violation_success(
        self, alert_service, mock_publisher, sample_violation, in_memory_violation_repo
    ):
        """Test resolving a violation."""
        # Save violation to repo
        await in_memory_violation_repo.save(sample_violation)

        command = ResolveViolationCommand(
            violation_id=sample_violation.id,
            notes="Maintenance completed",
            action_taken="Filter replaced",
        )

        result = await alert_service.resolve_violation(command)

        assert result.status == "RESOLVED"
        assert result.notes == "Maintenance completed"
        assert result.action_taken == "Filter replaced"

    @pytest.mark.anyio
    async def test_resolve_nonexistent_violation_raises(
        self, alert_service, mock_publisher
    ):
        """Test that resolving a nonexistent violation raises."""
        command = ResolveViolationCommand(
            violation_id=uuid4(),
            notes="Test",
        )

        with pytest.raises(ViolationNotFoundError):
            await alert_service.resolve_violation(command)


class TestAlertServiceGetViolations:
    """Tests for AlertApplicationService query methods."""

    @pytest.mark.anyio
    async def test_get_active_violations(
        self, alert_service, sample_violation, in_memory_violation_repo
    ):
        """Test getting active (open) violations."""
        await in_memory_violation_repo.save(sample_violation)

        violations = await alert_service.get_active_violations()

        assert len(violations) == 1
        assert violations[0].id == sample_violation.id

    @pytest.mark.anyio
    async def test_get_violations_by_factory(
        self, alert_service, sample_violation, sample_factory_id, in_memory_violation_repo
    ):
        """Test getting violations by factory ID."""
        await in_memory_violation_repo.save(sample_violation)

        violations = await alert_service.get_violations_by_factory(
            factory_id=sample_factory_id
        )

        assert len(violations) == 1
        assert violations[0].factory_id == sample_factory_id

    @pytest.mark.anyio
    async def test_get_violations_by_severity(
        self, alert_service, sample_violation, in_memory_violation_repo
    ):
        """Test getting violations by severity."""
        await in_memory_violation_repo.save(sample_violation)

        violations = await alert_service.get_violations_by_severity(
            severity="WARNING"
        )

        assert len(violations) == 1
        assert violations[0].severity == "WARNING"

    @pytest.mark.anyio
    async def test_get_violations_with_query_object(
        self, alert_service, sample_violation, in_memory_violation_repo
    ):
        """Test getting violations using query object."""
        await in_memory_violation_repo.save(sample_violation)

        query = GetViolationsQuery(
            status="OPEN",
            skip=0,
            limit=10,
        )

        violations = await alert_service.get_violations(query)

        assert len(violations) == 1

    @pytest.mark.anyio
    async def test_count_violations(
        self, alert_service, sample_violation, in_memory_violation_repo
    ):
        """Test counting violations."""
        await in_memory_violation_repo.save(sample_violation)

        count = await alert_service.count_violations(status="OPEN")

        assert count == 1


class TestAlertServiceAlertConfigs:
    """Tests for AlertApplicationService alert config methods."""

    @pytest.mark.anyio
    async def test_create_alert_config(
        self, alert_service, in_memory_alert_config_repo
    ):
        """Test creating an alert configuration."""
        config = await alert_service.create_alert_config(
            name="NO2 Limit",
            pollutant="no2",
            warning_threshold=40.0,
            high_threshold=80.0,
            critical_threshold=200.0,
        )

        assert config is not None
        assert config.pollutant == "no2"
        assert config.name == "NO2 Limit"

    @pytest.mark.anyio
    async def test_get_active_alert_configs(
        self, alert_service, sample_alert_config, in_memory_alert_config_repo
    ):
        """Test getting active alert configurations."""
        await in_memory_alert_config_repo.save(sample_alert_config)

        configs = await alert_service.get_active_alert_configs()

        assert len(configs) == 1
        assert configs[0].is_active is True

    @pytest.mark.anyio
    async def test_update_alert_config(
        self, alert_service, sample_alert_config, in_memory_alert_config_repo
    ):
        """Test updating an alert configuration."""
        await in_memory_alert_config_repo.save(sample_alert_config)

        updated = await alert_service.update_alert_config(
            config_id=sample_alert_config.id,
            name="Updated PM2.5 Limit",
            notify_sms=True,
        )

        assert updated.name == "Updated PM2.5 Limit"
        assert updated.notify_sms is True

    @pytest.mark.anyio
    async def test_update_nonexistent_config_raises(
        self, alert_service, in_memory_alert_config_repo
    ):
        """Test that updating a nonexistent config raises."""
        from src.domain.exceptions.alert_exceptions import AlertConfigNotFoundError

        with pytest.raises(AlertConfigNotFoundError):
            await alert_service.update_alert_config(
                config_id=uuid4(),
                name="Test",
            )

    @pytest.mark.anyio
    async def test_get_alert_config_by_id(
        self, alert_service, sample_alert_config, in_memory_alert_config_repo
    ):
        """Test getting an alert configuration by ID."""
        await in_memory_alert_config_repo.save(sample_alert_config)

        config = await alert_service.get_alert_config_by_id(sample_alert_config.id)

        assert config is not None
        assert config.id == sample_alert_config.id

    @pytest.mark.anyio
    async def test_get_nonexistent_config_returns_none(
        self, alert_service, in_memory_alert_config_repo
    ):
        """Test that getting a nonexistent config returns None."""
        config = await alert_service.get_alert_config_by_id(uuid4())

        assert config is None
