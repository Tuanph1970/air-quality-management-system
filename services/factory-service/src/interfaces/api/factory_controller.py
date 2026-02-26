"""Factory API controller."""
from fastapi import APIRouter

router = APIRouter(prefix="/factories", tags=["factories"])


@router.post("")
async def create_factory():
    pass


@router.get("")
async def list_factories():
    pass


@router.get("/{factory_id}")
async def get_factory(factory_id: str):
    pass


@router.put("/{factory_id}")
async def update_factory(factory_id: str):
    pass


@router.post("/{factory_id}/suspend")
async def suspend_factory(factory_id: str):
    pass


@router.post("/{factory_id}/resume")
async def resume_factory(factory_id: str):
    pass
