from __future__ import annotations

import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from webnc.logging_config import logger
import asyncio

from fastapi import HTTPException

from webnc.operations.base import AbstractOperation, OperationResult, OperationStatus

POLL_TTL = 300
CLEANUP_INTERVAL = 60


class OperationQueue:
    def __init__(self, max_workers: int = 4):
        self._queue: queue.Queue[Optional[AbstractOperation]] = queue.Queue()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="op"
        )
        self._operations: dict[str, AbstractOperation] = {}
        self._lock = threading.Lock()
        self._shutdown = False

        self._dispatcher = threading.Thread(target=self._dispatch_loop, daemon=True, name="op-dispatcher")
        self._dispatcher.start()

    def add_operation(self, op: AbstractOperation) -> str:
        if self._shutdown:
            raise RuntimeError("OperationQueue is shut down")

        op.status = OperationStatus.QUEUED
        with self._lock:
            self._operations[op.operation_id] = op
        self._queue.put(op)
        logger.info("Operation %s (%s) queued", op.operation_id, type(op).__name__)
        return op.operation_id

    def get_operation(self, op_id: str) -> Optional[AbstractOperation]:
        with self._lock:
            return self._operations.get(op_id)

    def cancel_operation(self, op_id: str) -> bool:
        op = self.get_operation(op_id)
        if not op:
            return False
        op.cancel()
        logger.info("Operation %s cancel requested", op_id)
        return True

    def _dispatch_loop(self) -> None:
        while not self._shutdown:
            try:
                op = self._queue.get(timeout=1)
                if op is None:
                    continue
                self._executor.submit(self._run_operation, op)
                self._queue.task_done()
            except queue.Empty:
                continue

    @staticmethod
    def _run_operation(op: AbstractOperation) -> None:
        try:
            op.run()
            op._finished_at = time.time()
            logger.info("Operation %s finished: %s", op.operation_id, op.status.value)
        except Exception as e:
            logger.exception("Operation %s crashed in runner: %s", op.operation_id, e)

    async def run_sync(self, op: AbstractOperation, timeout: float = 10.0):
        """Execute an operation in the thread pool and await the result.
        Used for quick operations where frontend expects a direct response."""
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(self._executor, op.run),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            op.status = OperationStatus.FAILED
            op.result = OperationResult(success=False, error_message=f"Operation timed out after {timeout}s")
            raise

        if op.status == OperationStatus.SUCCESS:
            return op.result.data if op.result else None
        else:
            msg = op.result.error_message if op.result else "Operation failed"
            raise HTTPException(status_code=400, detail=msg)

    def num_queued(self) -> int:
        return self._queue.qsize()

    def cleanup_old(self) -> int:
        now = time.time()
        keep = set()
        removed = 0
        with self._lock:
            for oid, op in list(self._operations.items()):
                if op.is_finished() and getattr(op, "_finished_at", now) < now - POLL_TTL:
                    del self._operations[oid]
                    removed += 1
                elif op.is_finished():
                    keep.add(oid)
        if removed:
            logger.info("Cleaned up %d stale operations, %d remaining", removed, len(keep))
        return removed

    def shutdown(self, wait: bool = True) -> None:
        logger.info("OperationQueue shutting down...")
        self._shutdown = True
        self._executor.shutdown(wait=wait)
