from fastapi import APIRouter, Depends, Request

from webnc.logging_config import logger
from webnc.operations.system import SystemInfoOperation
from webnc.operations.queue import OperationQueue
from webnc.version import VERSION

router = APIRouter()
FS_TIMEOUT = 10.0


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


@router.get("/api/sysinfo")
async def system_info(queue: OperationQueue = Depends(get_queue)):
    logger.info("GET /api/sysinfo")
    op = SystemInfoOperation()
    return await queue.run_sync(op, timeout=FS_TIMEOUT)


@router.get("/api/health")
async def health(request: Request):
    logger.info("GET /api/health")
    state = getattr(request.app.state, "server_state", "unknown")
    return {"status": state, "state": state, "version": VERSION}
