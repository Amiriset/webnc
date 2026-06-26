from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from webnc.logging_config import logger
from webnc.operations.archive import ArchiveListOperation
from webnc.operations.queue import OperationQueue

router = APIRouter()


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


@router.get("/api/archive/list")
async def archive_list(
    path: str = Query(...),
    password: Optional[str] = Query(None),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("GET /api/archive/list  path=%s password=%s",
                path, "***" if password else "none")
    op = ArchiveListOperation(path=path, password=password)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}
