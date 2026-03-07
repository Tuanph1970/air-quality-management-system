"""SQLAlchemy implementation of StationRepository."""
from __future__ import annotations

import logging
from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.station import Station
from ...domain.repositories.station_repository import StationRepository
from ...domain.value_objects.station_type import StationType
from ...domain.value_objects.geographic_coordinate import GeographicCoordinate
from .models import StationModel

logger = logging.getLogger(__name__)


class SQLAlchemyStationRepository(StationRepository):
    """SQLAlchemy implementation of StationRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: AsyncSession instance
        """
        self.session = session
    
    def _to_entity(self, model: StationModel) -> Station:
        """Convert SQLAlchemy model to domain entity.
        
        Args:
            model: StationModel instance
            
        Returns:
            Station entity
        """
        return Station(
            id=UUID(model.id),
            station_code=model.station_code,
            name=model.name,
            station_type=StationType.from_string(model.station_type),
            location=GeographicCoordinate.create(
                latitude=model.latitude,
                longitude=model.longitude,
                altitude=model.altitude,
            ),
            api_config=model.api_config,
            is_active=model.is_active,
            data_retention_days=model.data_retention_days,
            metadata=model.metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_data_received=model.last_data_received,
        )
    
    def _to_model(self, entity: Station) -> StationModel:
        """Convert domain entity to SQLAlchemy model.
        
        Args:
            entity: Station entity
            
        Returns:
            StationModel instance
        """
        return StationModel(
            id=str(entity.id),
            station_code=entity.station_code,
            name=entity.name,
            station_type=entity.station_type.value,
            latitude=entity.location.latitude,
            longitude=entity.location.longitude,
            altitude=entity.location.altitude,
            api_config=entity.api_config,
            is_active=entity.is_active,
            data_retention_days=entity.data_retention_days,
            metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_data_received=entity.last_data_received,
        )
    
    async def get_by_id(self, station_id: UUID) -> Optional[Station]:
        """Get station by ID."""
        result = await self.session.execute(
            select(StationModel).where(StationModel.id == str(station_id))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_station_code(self, station_code: str) -> Optional[Station]:
        """Get station by external station code."""
        result = await self.session.execute(
            select(StationModel).where(StationModel.station_code == station_code)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def list_all(
        self,
        station_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Station]:
        """List stations with optional filters."""
        query = select(StationModel)
        
        if station_type:
            query = query.where(StationModel.station_type == station_type.upper())
        if is_active is not None:
            query = query.where(StationModel.is_active == is_active)
        
        query = query.offset(skip).limit(limit).order_by(StationModel.created_at.desc())
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 10,
    ) -> List[Station]:
        """Find stations near a location using Haversine formula.
        
        Note: For production use with large datasets, consider using
        PostGIS or MySQL 8.0+ spatial functions for better performance.
        """
        # Get all active stations and filter in memory
        # (For production, implement spatial indexing)
        result = await self.session.execute(
            select(StationModel).where(StationModel.is_active == True)
        )
        models = result.scalars().all()
        
        # Calculate distances and filter
        nearby = []
        lat1, lon1 = radians(latitude), radians(longitude)
        R = 6371.0  # Earth radius in km
        
        for model in models:
            lat2, lon2 = radians(model.latitude), radians(model.longitude)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c
            
            if distance <= radius_km:
                station = self._to_entity(model)
                station.metadata["distance_km"] = round(distance, 2)
                nearby.append(station)
        
        # Sort by distance and limit
        nearby.sort(key=lambda s: s.metadata.get("distance_km", float('inf')))
        return nearby[:limit]
    
    async def save(self, station: Station) -> Station:
        """Save a station."""
        model = self._to_model(station)
        
        # Check if exists
        existing = await self.session.get(StationModel, model.id)
        if existing:
            # Update existing
            for key, value in model.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            await self.session.flush()
            logger.debug(f"Updated station: {station.station_code}")
        else:
            # Insert new
            self.session.add(model)
            await self.session.flush()
            logger.debug(f"Created station: {station.station_code}")
        
        return station
    
    async def delete(self, station_id: UUID) -> bool:
        """Delete a station."""
        result = await self.session.execute(
            select(StationModel).where(StationModel.id == str(station_id))
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            logger.info(f"Deleted station: {model.station_code}")
            return True
        
        return False
    
    async def count(self, station_type: Optional[str] = None) -> int:
        """Count stations."""
        query = select(func.count(StationModel.id))
        
        if station_type:
            query = query.where(StationModel.station_type == station_type.upper())
        
        result = await self.session.execute(query)
        return result.scalar() or 0
