"""PurpleAir ingestion service routes — proxy requests to purpleair-ingestion-service."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..utils.service_client import ServiceClient
from ..config import settings

router = APIRouter(prefix="/api/v1/purpleair", tags=["purpleair"])


@router.post("/webhook")
async def purpleair_webhook(request: Request):
    """PurpleAir device webhook endpoint.
    
    Receive data from PurpleAir Flex-Air Quality Monitors.
    Devices can be configured to push data to this endpoint.
    """
    client = ServiceClient(settings.PURPLEAIR_INGESTION_SERVICE_URL)
    return await client.forward_request(request, "/api/v1/purpleair/webhook")


@router.post("/register")
async def register_purpleair_sensor(request: Request):
    """Register a PurpleAir sensor."""
    client = ServiceClient(settings.PURPLEAIR_INGESTION_SERVICE_URL)
    return await client.forward_request(request, "/api/v1/purpleair/register")


@router.get("/fake-data")
async def generate_fake_purpleair_data(request: Request):
    """Generate fake PurpleAir data for demonstration."""
    client = ServiceClient(settings.PURPLEAIR_INGESTION_SERVICE_URL)
    return await client.forward_request(request, "/api/v1/purpleair/fake-data")
