from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from webnc.logging_config import logger
from webnc.operations.queue import OperationQueue

router = APIRouter()


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


@router.get("/api/operation/{op_id}")
async def get_operation(op_id: str, queue: OperationQueue = Depends(get_queue)):
    logger.info("GET /api/operation/%s", op_id)
    op = queue.get_operation(op_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")

    return {
        "operation_id": op.operation_id,
        "status": op.status.value,
        "progress": op.progress,
        "progress_message": op.progress_message,
        "attempt": op.attempt,
        "max_retries": op.max_retries,
        "result": {
            "success": op.result.success,
            "data": op.result.data,
            "error_message": op.result.error_message,
        } if op.result else None,
    }


@router.post("/api/operation/{op_id}/cancel")
async def cancel_operation(op_id: str, queue: OperationQueue = Depends(get_queue)):
    logger.info("POST /api/operation/%s/cancel", op_id)
    ok = queue.cancel_operation(op_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Operation not found")
    return {"status": "cancelled"}
