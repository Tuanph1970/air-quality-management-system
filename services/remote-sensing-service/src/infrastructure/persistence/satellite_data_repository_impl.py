"""SQLAlchemy implementation of SatelliteDataRepository."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.satellite_data import SatelliteData
from ...domain.repositories.satellite_data_repository import SatelliteDataRepository
from ...domain.value_objects.geo_polygon import GeoPolygon
from ...domain.value_objects.grid_cell import GridCell
from ...domain.value_objects.quality_flag import QualityFlag
from ...domain.value_objects.satellite_source import SatelliteSource
from .models import SatelliteDataModel

logger = logging.getLogger(__name__)


class SQLAlchemySatelliteDataRepository(SatelliteDataRepository):
    """Repository implementation backed by PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, data_id: UUID) -> Optional[SatelliteData]:
        result = await self.session.execute(
            select(SatelliteDataModel).where(SatelliteDataModel.id == data_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest(
        self, source: SatelliteSource, data_type: str
    ) -> Optional[SatelliteData]:
        result = await self.session.execute(
            select(SatelliteDataModel)
            .where(
                SatelliteDataModel.source == source.value,
                SatelliteDataModel.data_type == data_type,
            )
            .order_by(SatelliteDataModel.observation_time.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_time_range(
        self,
        source: SatelliteSource,
        start_time: datetime,
        end_time: datetime,
        bbox: Optional[GeoPolygon] = None,
    ) -> List[SatelliteData]:
        stmt = (
            select(SatelliteDataModel)
            .where(
                SatelliteDataModel.source == source.value,
                SatelliteDataModel.observation_time >= start_time,
                SatelliteDataModel.observation_time <= end_time,
            )
            .order_by(SatelliteDataModel.observation_time.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, data: SatelliteData) -> SatelliteData:
        model = self._to_model(data)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return self._to_entity(merged)

    async def delete_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            delete(SatelliteDataModel).where(
                SatelliteDataModel.observation_time < cutoff
            )
        )
        await self.session.commit()
        return result.rowcount

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    def _to_entity(self, model: SatelliteDataModel) -> SatelliteData:
        grid_cells = [
            GridCell(
                lat=c["lat"],
                lon=c["lon"],
                value=c["value"],
                uncertainty=c.get("uncertainty", 0.0),
            )
            for c in (model.grid_cells or [])
        ]
        bbox_data = model.bbox or {}
        return SatelliteData(
            id=model.id,
            source=SatelliteSource(model.source),
            data_type=model.data_type,
            observation_time=model.observation_time,
            fetch_time=model.fetch_time,
            bbox=GeoPolygon(
                north=bbox_data.get("north", 0),
                south=bbox_data.get("south", 0),
                east=bbox_data.get("east", 0),
                west=bbox_data.get("west", 0),
            ),
            grid_cells=grid_cells,
            quality_flag=QualityFlag(model.quality_flag),
            metadata=model.metadata_json or {},
            file_path=model.file_path,
        )

    def _to_model(self, entity: SatelliteData) -> SatelliteDataModel:
        return SatelliteDataModel(
            id=entity.id,
            source=entity.source.value,
            data_type=entity.data_type,
            observation_time=entity.observation_time,
            fetch_time=entity.fetch_time,
            bbox=entity.bbox.to_dict(),
            grid_cells=[
                {
                    "lat": c.lat,
                    "lon": c.lon,
                    "value": c.value,
                    "uncertainty": c.uncertainty,
                }
                for c in entity.grid_cells
            ],
            quality_flag=entity.quality_flag.value,
            metadata_json=entity.metadata,
            file_path=entity.file_path,
        )
