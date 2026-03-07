"""Station application service - orchestrates station use cases."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..commands import (
    CreateStationCommand,
    UpdateStationCommand,
    ConfigureStationAPICommand,
    ActivateStationCommand,
    DeactivateStationCommand,
    IngestStationDataCommand,
    RecordStationReadingsCommand,
    DeleteStationCommand,
)
from ..queries import (
    GetStationQuery,
    GetStationByCodeQuery,
    ListStationsQuery,
    GetNearbyStationsQuery,
    GetStationReadingsQuery,
    GetLatestStationReadingsQuery,
)
from ..dto import (
    StationDTO,
    StationListDTO,
    PollutantReadingDTO,
    StationReadingsDTO,
    StationReadingsListDTO,
)
from ...domain.entities.station import Station
from ...domain.repositories import StationRepository, ReadingRepository
from ...domain.services import DataQualityValidator
from ...domain.exceptions.station_exceptions import (
    StationNotFoundError,
    StationAlreadyExistsError,
    InvalidStationConfigurationError,
    StationDataValidationError,
)

logger = logging.getLogger(__name__)


class StationApplicationService:
    """Application service for station management use cases.
    
    This service orchestrates commands and queries, coordinating between
    domain entities, repositories, and external services.
    """
    
    def __init__(
        self,
        station_repository: StationRepository,
        reading_repository: ReadingRepository,
        event_publisher: Any = None,
    ):
        """Initialize application service.
        
        Args:
            station_repository: Repository for stations
            reading_repository: Repository for readings
            event_publisher: Optional event publisher for domain events
        """
        self.station_repository = station_repository
        self.reading_repository = reading_repository
        self.event_publisher = event_publisher
        self.quality_validator = DataQualityValidator()
    
    # ==================================================================
    # Command Handlers (Write operations)
    # ==================================================================
    
    async def create_station(self, command: CreateStationCommand) -> StationDTO:
        """Create a new air quality station.
        
        Args:
            command: CreateStationCommand
            
        Returns:
            StationDTO of created station
            
        Raises:
            StationAlreadyExistsError: If station code already exists
        """
        # Check for duplicate station code
        existing = await self.station_repository.get_by_station_code(command.station_code)
        if existing:
            raise StationAlreadyExistsError(command.station_code, "station_code")
        
        # Create station using aggregate
        from ...domain.aggregates import StationAggregate
        
        aggregate = StationAggregate.create(
            name=command.name,
            station_code=command.station_code,
            station_type=command.station_type,
            latitude=command.latitude,
            longitude=command.longitude,
            altitude=command.altitude,
        )
        
        station = aggregate.station
        
        # Update with additional fields
        if command.metadata:
            station.metadata = command.metadata
        if command.data_retention_days:
            station.data_retention_days = command.data_retention_days
        
        # Save and publish events
        saved_station = await self.station_repository.save(station)
        
        # Publish domain events
        events = aggregate.collect_events()
        if self.event_publisher and events:
            for event in events:
                await self.event_publisher.publish(event)
        
        logger.info(f"Created station: {saved_station.station_code} ({saved_station.name})")
        return StationDTO.from_entity(saved_station)
    
    async def update_station(self, command: UpdateStationCommand) -> StationDTO:
        """Update station properties.
        
        Args:
            command: UpdateStationCommand
            
        Returns:
            StationDTO of updated station
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(command.station_id)
        if not station:
            raise StationNotFoundError(command.station_id)
        
        station.update(
            name=command.name,
            station_type=command.station_type,
            latitude=command.latitude,
            longitude=command.longitude,
            altitude=command.altitude,
            metadata=command.metadata,
            data_retention_days=command.data_retention_days,
        )
        
        saved_station = await self.station_repository.save(station)
        logger.info(f"Updated station: {saved_station.station_code}")
        
        return StationDTO.from_entity(saved_station)
    
    async def configure_station_api(self, command: ConfigureStationAPICommand) -> StationDTO:
        """Configure API endpoint for a station.
        
        Args:
            command: ConfigureStationAPICommand
            
        Returns:
            StationDTO of updated station
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(command.station_id)
        if not station:
            raise StationNotFoundError(command.station_id)
        
        station.configure_api(
            endpoint=command.endpoint,
            method=command.method,
            headers=command.headers,
            auth_type=command.auth_type,
            auth_credentials=command.auth_credentials,
            poll_interval_seconds=command.poll_interval_seconds,
            adapter_type=command.adapter_type,
            request_template=command.request_template,
            response_mapping=command.response_mapping,
        )
        
        saved_station = await self.station_repository.save(station)
        
        # Publish events
        events = station.collect_events()
        if self.event_publisher and events:
            for event in events:
                await self.event_publisher.publish(event)
        
        logger.info(f"Configured API for station: {saved_station.station_code}")
        return StationDTO.from_entity(saved_station)
    
    async def activate_station(self, command: ActivateStationCommand) -> StationDTO:
        """Activate a station.
        
        Args:
            command: ActivateStationCommand
            
        Returns:
            StationDTO of activated station
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(command.station_id)
        if not station:
            raise StationNotFoundError(command.station_id)
        
        station.activate()
        saved_station = await self.station_repository.save(station)
        
        # Publish events
        events = station.collect_events()
        if self.event_publisher and events:
            for event in events:
                await self.event_publisher.publish(event)
        
        logger.info(f"Activated station: {saved_station.station_code}")
        return StationDTO.from_entity(saved_station)
    
    async def deactivate_station(self, command: DeactivateStationCommand) -> StationDTO:
        """Deactivate a station.
        
        Args:
            command: DeactivateStationCommand
            
        Returns:
            StationDTO of deactivated station
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(command.station_id)
        if not station:
            raise StationNotFoundError(command.station_id)
        
        station.deactivate(reason=command.reason)
        saved_station = await self.station_repository.save(station)
        
        # Publish events
        events = station.collect_events()
        if self.event_publisher and events:
            for event in events:
                await self.event_publisher.publish(event)
        
        logger.info(f"Deactivated station: {saved_station.station_code}")
        return StationDTO.from_entity(saved_station)
    
    async def record_station_readings(
        self,
        command: RecordStationReadingsCommand,
    ) -> StationReadingsDTO:
        """Record readings from a station.
        
        Args:
            command: RecordStationReadingsCommand
            
        Returns:
            StationReadingsDTO with recorded readings
            
        Raises:
            StationNotFoundError: If station not found
            StationDataValidationError: If readings fail validation
        """
        station = await self.station_repository.get_by_id(command.station_id)
        if not station:
            raise StationNotFoundError(command.station_id)
        
        # Validate readings
        is_valid, error = self.quality_validator.validate_readings_batch(command.readings)
        if not is_valid:
            raise StationDataValidationError(error)
        
        # Use aggregate to record readings
        from ...domain.aggregates import StationAggregate
        
        aggregate = StationAggregate(station)
        batch = aggregate.record_readings(
            readings=command.readings,
            timestamp=command.timestamp,
            source=command.source,
        )
        
        # Save readings
        await self.reading_repository.save_batch(batch)
        
        # Save station (updates last_data_received)
        await self.station_repository.save(station)
        
        # Publish events
        events = aggregate.collect_events()
        if self.event_publisher and events:
            for event in events:
                await self.event_publisher.publish(event)
        
        logger.info(
            f"Recorded {batch.reading_count} readings from station {station.station_code}"
        )
        
        return StationReadingsDTO.from_batch(batch, station.name)
    
    async def delete_station(self, command: DeleteStationCommand) -> bool:
        """Delete a station.
        
        Args:
            command: DeleteStationCommand
            
        Returns:
            True if deleted
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(command.station_id)
        if not station:
            raise StationNotFoundError(command.station_id)
        
        result = await self.station_repository.delete(command.station_id)
        logger.info(f"Deleted station: {station.station_code}")
        return result
    
    # ==================================================================
    # Query Handlers (Read operations)
    # ==================================================================
    
    async def get_station(self, query: GetStationQuery) -> StationDTO:
        """Get station by ID.
        
        Args:
            query: GetStationQuery
            
        Returns:
            StationDTO
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(query.station_id)
        if not station:
            raise StationNotFoundError(query.station_id)
        
        return StationDTO.from_entity(station)
    
    async def get_station_by_code(self, query: GetStationByCodeQuery) -> StationDTO:
        """Get station by external code.
        
        Args:
            query: GetStationByCodeQuery
            
        Returns:
            StationDTO
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_station_code(query.station_code)
        if not station:
            raise StationNotFoundError(query.station_code)
        
        return StationDTO.from_entity(station)
    
    async def list_stations(self, query: ListStationsQuery) -> StationListDTO:
        """List stations with filters.
        
        Args:
            query: ListStationsQuery
            
        Returns:
            StationListDTO
        """
        stations = await self.station_repository.list_all(
            station_type=query.station_type,
            is_active=query.is_active,
            skip=query.skip,
            limit=query.limit,
        )
        
        total = await self.station_repository.count(query.station_type)
        
        items = [StationDTO.from_entity(s) for s in stations]
        return StationListDTO(items=items, total=total, skip=query.skip, limit=query.limit)
    
    async def get_nearby_stations(self, query: GetNearbyStationsQuery) -> StationListDTO:
        """Find stations near a location.
        
        Args:
            query: GetNearbyStationsQuery
            
        Returns:
            StationListDTO
        """
        stations = await self.station_repository.find_nearby(
            latitude=query.latitude,
            longitude=query.longitude,
            radius_km=query.radius_km,
            limit=query.limit,
        )
        
        items = [StationDTO.from_entity(s) for s in stations]
        return StationListDTO(items=items, total=len(items), skip=0, limit=len(items))
    
    async def get_station_readings(
        self,
        query: GetStationReadingsQuery,
    ) -> StationReadingsListDTO:
        """Get readings for a station.
        
        Args:
            query: GetStationReadingsQuery
            
        Returns:
            StationReadingsListDTO
        """
        # Verify station exists
        station = await self.station_repository.get_by_id(query.station_id)
        if not station:
            raise StationNotFoundError(query.station_id)
        
        # Parse timestamps
        start_time = None
        end_time = None
        
        if query.start_time:
            start_time = datetime.fromisoformat(query.start_time.replace('Z', '+00:00'))
        if query.end_time:
            end_time = datetime.fromisoformat(query.end_time.replace('Z', '+00:00'))
        
        readings = await self.reading_repository.get_by_station_id(
            station_id=query.station_id,
            start_time=start_time,
            end_time=end_time,
            pollutant_type=query.pollutant_type,
            skip=query.skip,
            limit=query.limit,
        )
        
        items = [PollutantReadingDTO.from_entity(r) for r in readings]
        return StationReadingsListDTO(
            items=items,
            total=len(items),  # Should get actual count from repo
            skip=query.skip,
            limit=query.limit,
        )
    
    async def get_latest_station_readings(
        self,
        query: GetLatestStationReadingsQuery,
    ) -> StationReadingsDTO:
        """Get latest readings for a station.
        
        Args:
            query: GetLatestStationReadingsQuery
            
        Returns:
            StationReadingsDTO
            
        Raises:
            StationNotFoundError: If station not found
        """
        station = await self.station_repository.get_by_id(query.station_id)
        if not station:
            raise StationNotFoundError(query.station_id)
        
        readings_dict = await self.reading_repository.get_latest_by_station(
            station_id=query.station_id,
            pollutant_types=query.pollutant_types,
        )
        
        readings_values = {
            pt: reading.value
            for pt, reading in readings_dict.items()
        }
        
        # Get latest timestamp
        latest_ts = None
        if readings_dict:
            latest_ts = max(r.timestamp for r in readings_dict.values())
        
        return StationReadingsDTO(
            station_id=station.id,
            station_name=station.name,
            timestamp=latest_ts or datetime.now(timezone.utc),
            readings=readings_values,
            source="API",
        )
