"""Tests for OperationQueue as an async operation boundary.

Verifies the lifecycle: add → poll → complete/fail → cleanup.
Not a parallel execution stress test — the queue's role is to decouple
long-running FS operations from HTTP request handling.
"""
import threading
import time
import uuid

import pytest

from webnc.operations.base import AbstractOperation, OperationResult, OperationStatus
from webnc.operations.queue import OperationQueue, POLL_TTL


# ── Test operations ──────────────────────────────────────────────────────────

class ImmediateSuccessOp(AbstractOperation[str]):
    def execute(self):
        return OperationResult(success=True, data="done")


class ImmediateFailOp(AbstractOperation[str]):
    def execute(self):
        return OperationResult(success=False, error_message="disk full")


class CrashOp(AbstractOperation[str]):
    def execute(self):
        raise RuntimeError("unexpected crash")


class SlowOp(AbstractOperation[str]):
    def execute(self):
        time.sleep(0.3)
        return OperationResult(success=True, data="slow-ok")


class BlockingOp(AbstractOperation[str]):
    """Blocks until release() is called — lets us test cancel semantics."""
    _start_event = threading.Event()
    _proceed_event = threading.Event()

    def execute(self):
        BlockingOp._start_event.set()
        BlockingOp._proceed_event.wait(timeout=10)
        return OperationResult(success=True, data="released")

    @classmethod
    def release(cls):
        cls._proceed_event.set()

    @classmethod
    def reset(cls):
        cls._start_event = threading.Event()
        cls._proceed_event = threading.Event()


class NonRetriableFailOp(AbstractOperation[str]):
    def execute(self):
        raise PermissionError("access denied")


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def q():
    BlockingOp.reset()
    queue = OperationQueue(max_workers=2)
    yield queue
    BlockingOp.release()
    queue.shutdown(wait=False)


def _wait_finished(q: OperationQueue, op_id: str, timeout: float = 5.0):
    """Poll until operation reaches a terminal status."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        op = q.get_operation(op_id)
        if op and op.is_finished():
            return op
        time.sleep(0.05)
    raise TimeoutError(f"Operation {op_id} did not finish within {timeout}s")


# ── Tests ────────────────────────────────────────────────────────────────────

class TestLifecycleSuccess:
    def test_queued_to_completed(self, q):
        op = ImmediateSuccessOp()
        op_id = q.add_operation(op)
        assert q.get_operation(op_id) is not None

        finished = _wait_finished(q, op_id)
        assert finished.status == OperationStatus.SUCCESS
        assert finished.result.success is True
        assert finished.result.data == "done"

    def test_poll_result_structure(self, q):
        op = ImmediateSuccessOp()
        op_id = q.add_operation(op)
        finished = _wait_finished(q, op_id)

        result = finished.result
        assert result.success is True
        assert result.data == "done"
        assert result.error_message is None


class TestLifecycleFailure:
    def test_queued_to_failed(self, q):
        op = ImmediateFailOp()
        op_id = q.add_operation(op)

        finished = _wait_finished(q, op_id)
        assert finished.status == OperationStatus.FAILED
        assert finished.result.success is False
        assert "disk full" in finished.result.error_message

    def test_crash_to_failed(self, q):
        op = CrashOp(max_retries=0)
        op_id = q.add_operation(op)

        finished = _wait_finished(q, op_id)
        assert finished.status == OperationStatus.FAILED
        assert "unexpected crash" in finished.result.error_message

    def test_non_retriable_error_fails_immediately(self, q):
        op = NonRetriableFailOp(max_retries=3)
        op_id = q.add_operation(op)

        finished = _wait_finished(q, op_id)
        assert finished.status == OperationStatus.FAILED
        assert finished.attempt == 1


class TestCancel:
    def test_cancel_sets_flag(self, q):
        """Cancel sets the flag — operation checks it between retries."""
        op = SlowOp()
        op_id = q.add_operation(op)
        q.cancel_operation(op_id)

        finished = _wait_finished(q, op_id)
        assert finished.cancel_requested is True

    def test_cancel_before_run_aborts(self, q):
        """Cancel before run() sees it immediately."""
        from webnc.operations.base import AbstractOperation, OperationResult

        class DelayedOp(AbstractOperation[str]):
            def execute(self):
                return OperationResult(success=True, data="ok")

        op = DelayedOp()
        op.cancel()
        op.run()
        assert op.status == OperationStatus.CANCELLED

    def test_cancel_returns_true_for_existing(self, q):
        op = SlowOp()
        op_id = q.add_operation(op)
        assert q.cancel_operation(op_id) is True
        _wait_finished(q, op_id)

    def test_cancel_returns_false_for_unknown(self, q):
        assert q.cancel_operation(str(uuid.uuid4())) is False


class TestNotFound:
    def test_get_unknown_operation_returns_none(self, q):
        assert q.get_operation(str(uuid.uuid4())) is None

    def test_get_returns_operation_object(self, q):
        op = ImmediateSuccessOp()
        op_id = q.add_operation(op)
        retrieved = q.get_operation(op_id)
        assert retrieved is op


class TestCleanup:
    def test_cleanup_removes_expired_operations(self, q):
        op = ImmediateSuccessOp()
        op_id = q.add_operation(op)
        _wait_finished(q, op_id)

        op = q.get_operation(op_id)
        op._finished_at = time.time() - POLL_TTL - 1

        removed = q.cleanup_old()
        assert removed >= 1
        assert q.get_operation(op_id) is None

    def test_cleanup_keeps_recent_operations(self, q):
        op = ImmediateSuccessOp()
        op_id = q.add_operation(op)
        _wait_finished(q, op_id)

        removed = q.cleanup_old()
        assert removed == 0
        assert q.get_operation(op_id) is not None

    def test_cleanup_does_not_remove_running(self, q):
        op = SlowOp()
        op_id = q.add_operation(op)
        time.sleep(0.05)

        removed = q.cleanup_old()
        assert removed == 0
        assert q.get_operation(op_id) is not None
        _wait_finished(q, op_id)


class TestNonBlocking:
    def test_add_operation_returns_instantly(self, q):
        """add_operation() is a quick enqueue, not a blocking execute."""
        op = SlowOp()
        start = time.time()
        op_id = q.add_operation(op)
        elapsed = time.time() - start

        assert elapsed < 0.1
        assert op_id is not None
        assert q.get_operation(op_id) is not None
        _wait_finished(q, op_id)

    def test_slow_operation_does_not_block_add(self, q):
        ops = []
        for _ in range(3):
            op = SlowOp()
            ops.append(q.add_operation(op))

        for op_id in ops:
            assert q.get_operation(op_id) is not None

        for op_id in ops:
            _wait_finished(q, op_id)


class TestQueueState:
    def test_shutdown_rejects_new_operations(self, q):
        q.shutdown(wait=False)
        with pytest.raises(RuntimeError, match="shut down"):
            q.add_operation(ImmediateSuccessOp())

    def test_registry_tracks_operations(self, q):
        """Operations are tracked in the internal registry after add."""
        assert q.get_operation("nonexistent") is None
        op = ImmediateSuccessOp()
        op_id = q.add_operation(op)
        assert q.get_operation(op_id) is not None
        _wait_finished(q, op_id)
