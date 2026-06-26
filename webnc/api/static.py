import asyncio
import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from webnc.logging_config import logger

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT_DIR = PROJECT_ROOT / "client"


async def _file_exists(path: Path) -> bool:
    return await asyncio.to_thread(path.exists)


async def _is_file(path: Path) -> bool:
    return await asyncio.to_thread(path.is_file)


@router.get("/")
async def serve_index():
    logger.info("GET /  \u2192 index.html")
    return FileResponse(CLIENT_DIR / "index.html")


@router.get("/css/{rest:path}")
async def serve_css(rest: str):
    file = CLIENT_DIR / "css" / rest
    if not await _file_exists(file) or not await _is_file(file):
        raise HTTPException(status_code=404)
    mime = mimetypes.guess_type(str(file))[0] or "text/css"
    return FileResponse(file, media_type=mime)


@router.get("/js/{rest:path}")
async def serve_js(rest: str):
    file = CLIENT_DIR / "js" / rest
    if not await _file_exists(file) or not await _is_file(file):
        raise HTTPException(status_code=404)
    mime = "text/javascript" if file.suffix == ".js" else mimetypes.guess_type(str(file))[0]
    return FileResponse(file, media_type=mime or "application/octet-stream")
