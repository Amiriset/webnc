from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


def get_config_manager():
    from webnc.main import config_manager
    return config_manager


@router.get("/api/config")
async def get_config():
    cm = get_config_manager()
    return cm.get_raw()


@router.put("/api/config")
async def update_config(data: dict):
    cm = get_config_manager()
    cm.set_raw(data)
    return {"status": "ok"}
