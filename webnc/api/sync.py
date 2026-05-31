from fastapi import APIRouter, Depends

from webnc.logging_config import logger
from webnc.models.sync import SyncRequest, SyncExecuteRequest
from webnc.operations.syncop import SyncPlanOperation, SyncExecuteOperation
from webnc.operations.queue import OperationQueue

router = APIRouter()


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


@router.post("/api/sync/plan")
async def sync_plan(
    req: SyncRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/sync/plan  left=%s right=%s subdirs=%s ignore_date=%s asymmetric=%s",
                req.left, req.right, req.subdirs, req.ignore_date, req.asymmetric)
    op = SyncPlanOperation(
        left=req.left, right=req.right,
        subdirs=req.subdirs, by_content=req.by_content,
        ignore_date=req.ignore_date, asymmetric=req.asymmetric,
        filter=req.filter,
    )
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}


@router.post("/api/sync/execute")
async def sync_execute(
    req: SyncExecuteRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/sync/execute  left=%s right=%s actions=%d",
                req.left, req.right, len(req.actions))
    op = SyncExecuteOperation(left=req.left, right=req.right, actions=req.actions)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}
