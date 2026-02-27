"""SQLAlchemy implementation of FusedDataRepository."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.fused_data import FusedData, FusedDataPoint
from ...domain.repositories.fused_data_repository import FusedDataRepository
from ...domain.value_objects.geo_polygon import GeoPolygon
from .models import FusedDataModel

logger = logging.getLogger(__name__)


class SQLAlchemyFusedDataRepository(FusedDataRepository):
    """Repository implementation for fused data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, fusion_id: UUID) -> Optional[FusedData]:
        result = await self.session.execute(
            select(FusedDataModel).where(FusedDataModel.id == fusion_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest(self, pollutant: str = "") -> Optional[FusedData]:
        stmt = select(FusedDataModel).order_by(FusedDataModel.created_at.desc())
        if pollutant:
            stmt = stmt.where(FusedDataModel.pollutant == pollutant)
        stmt = stmt.limit(1)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        pollutant: str = "",
    ) -> List[FusedData]:
        stmt = (
            select(FusedDataModel)
            .where(
                FusedDataModel.created_at >= start_time,
                FusedDataModel.created_at <= end_time,
            )
            .order_by(FusedDataModel.created_at.desc())
        )
        if pollutant:
            stmt = stmt.where(FusedDataModel.pollutant == pollutant)

        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, fused: FusedData) -> FusedData:
        model = self._to_model(fused)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return self._to_entity(merged)

    async def delete_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            delete(FusedDataModel).where(FusedDataModel.created_at < cutoff)
        )
        await self.session.commit()
        return result.rowcount

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    def _to_entity(self, model: FusedDataModel) -> FusedData:
        bbox_data = model.bbox or {}
        data_points = [
            FusedDataPoint(
                lat=dp["lat"],
                lon=dp["lon"],
                fused_value=dp["fused_value"],
                confidence=dp["confidence"],
                sources=dp.get("sources", []),
                source_values=dp.get("source_values", {}),
            )
            for dp in (model.data_points or [])
        ]
        return FusedData(
            id=model.id,
            sources_used=model.sources_used or [],
            bbox=GeoPolygon(
                north=bbox_data.get("north", 0),
                south=bbox_data.get("south", 0),
                east=bbox_data.get("east", 0),
                west=bbox_data.get("west", 0),
            ),
            time_range_start=model.time_range_start,
            time_range_end=model.time_range_end,
            data_points=data_points,
            pollutant=model.pollutant,
            metadata=model.metadata_json or {},
            created_at=model.created_at,
        )

    def _to_model(self, entity: FusedData) -> FusedDataModel:
        return FusedDataModel(
            id=entity.id,
            sources_used=entity.sources_used,
            bbox=entity.bbox.to_dict(),
            time_range_start=entity.time_range_start,
            time_range_end=entity.time_range_end,
            data_points=[
                {
                    "lat": dp.lat,
                    "lon": dp.lon,
                    "fused_value": dp.fused_value,
                    "confidence": dp.confidence,
                    "sources": dp.sources,
                    "source_values": dp.source_values,
                }
                for dp in entity.data_points
            ],
            average_confidence=entity.average_confidence,
            pollutant=entity.pollutant,
            metadata_json=entity.metadata,
            created_at=entity.created_at,
        )
