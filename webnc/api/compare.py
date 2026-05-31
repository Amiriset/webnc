from fastapi import APIRouter, Depends

from webnc.logging_config import logger
from webnc.models.compare import CompareRequest
from webnc.operations.compare import CompareOperation
from webnc.operations.queue import OperationQueue

router = APIRouter()


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


@router.post("/api/compare")
async def compare_directories(
    req: CompareRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/compare  left=%s right=%s", req.left, req.right)
    op = CompareOperation(left=req.left, right=req.right)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}
