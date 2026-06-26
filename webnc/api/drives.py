from fastapi import APIRouter, Depends, HTTPException, Query

from webnc.logging_config import logger
from webnc.operations.drives import ListDrivesOperation, DiskUsageOperation
from webnc.operations.queue import OperationQueue

router = APIRouter()
FS_TIMEOUT = 10.0


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


@router.get("/api/drives")
async def list_drives(queue: OperationQueue = Depends(get_queue)):
    logger.info("GET /api/drives")
    op = ListDrivesOperation()
    return await queue.run_sync(op, timeout=FS_TIMEOUT)


@router.get("/api/disk")
async def disk_usage(
    path: str = Query("/C/", description="Path or drive root to check"),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("GET /api/disk  path=%s", path)
    op = DiskUsageOperation(path=path)
    return await queue.run_sync(op, timeout=FS_TIMEOUT)
