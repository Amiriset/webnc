import asyncio
import os

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from webnc.logging_config import logger
from webnc.vfs.paths import safe_path


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "cp866", "cp1251", "cp437", "latin-1"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return data.decode("utf-8", errors="replace")


def _get_cm():
    from webnc.main import config_manager
    return config_manager


router = APIRouter()


class ExecRequest(BaseModel):
    command: str
    cwd: str = ""


class ExecResponse(BaseModel):
    stdout: str
    stderr: str
    returncode: int


@router.post("/api/exec", response_model=ExecResponse)
async def exec_command(req: ExecRequest):
    cmd = req.command.strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Empty command")

    prog = cmd.split(maxsplit=1)[0].lower()
    cm = _get_cm()
    allowed = cm.get_exec_allowed()
    if allowed and prog not in allowed:
        raise HTTPException(status_code=403, detail=f"Command '{prog}' is not allowed")
    denied = cm.get_exec_denied()
    if prog in denied:
        raise HTTPException(status_code=403, detail=f"Command '{prog}' is denied")

    logger.info("POST /api/exec  cmd=%s cwd=%s", cmd, req.cwd)
    cwd = str(safe_path(req.cwd)) if req.cwd else os.getcwd()
    exec_timeout = cm.get_exec_timeout()
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=exec_timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise HTTPException(status_code=408, detail=f"Command timed out ({exec_timeout}s)")
        return ExecResponse(
            stdout=_decode(stdout),
            stderr=_decode(stderr),
            returncode=proc.returncode or 0,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Command not found")
    except Exception as e:
        logger.exception("Exec failed")
        raise HTTPException(status_code=500, detail=str(e))
