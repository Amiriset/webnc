"""Tests for webnc.operations.base — retry, cancel, backoff logic."""
import time
from unittest.mock import MagicMock, patch

import pytest

from webnc.operations.base import (
    AbstractOperation,
    OperationResult,
    OperationStatus,
)


class SuccessOperation(AbstractOperation[str]):
    def execute(self):
        return OperationResult(success=True, data="ok")


class FailOperation(AbstractOperation[str]):
    def execute(self):
        return OperationResult(success=False, error_message="fail")


class CrashOnceOperation(AbstractOperation[str]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._call_count = 0

    def execute(self):
        self._call_count += 1
        if self._call_count == 1:
            raise ValueError("transient error")
        return OperationResult(success=True, data="recovered")


class CrashAlwaysOperation(AbstractOperation[str]):
    def execute(self):
        raise RuntimeError("permanent error")


class NonRetriableErrorOperation(AbstractOperation[str]):
    def execute(self):
        raise PermissionError("access denied")


class TestOperationStatus:
    def test_enum_values(self):
        assert OperationStatus.CREATED.value == "CREATED"
        assert OperationStatus.SUCCESS.value == "SUCCESS"
        assert OperationStatus.FAILED.value == "FAILED"
        assert OperationStatus.CANCELLED.value == "CANCELLED"


class TestOperationResult:
    def test_success_with_data(self):
        r = OperationResult(success=True, data="hello")
        assert r.success is True
        assert r.data == "hello"
        assert r.error_message is None

    def test_failure_with_error(self):
        r = OperationResult(success=False, error_message="boom")
        assert r.success is False
        assert r.error_message == "boom"


class TestRun:
    def test_success_on_first_attempt(self):
        op = SuccessOperation()
        op.run()
        assert op.status == OperationStatus.SUCCESS
        assert op.result.success is True
        assert op.result.data == "ok"

    def test_immediate_failure(self):
        op = FailOperation()
        op.run()
        assert op.status == OperationStatus.FAILED
        assert op.result.success is False

    def test_retry_on_exception(self):
        op = CrashOnceOperation(max_retries=3)
        with patch.object(op, "backoff_delay", return_value=0.01):
            op.run()
        assert op.status == OperationStatus.SUCCESS
        assert op.result.data == "recovered"
        assert op.attempt == 2

    def test_max_retries_exhausted(self):
        op = CrashAlwaysOperation(max_retries=2)
        with patch.object(op, "backoff_delay", return_value=0.01):
            op.run()
        assert op.status == OperationStatus.FAILED
        assert "permanent error" in op.result.error_message

    def test_no_retries_when_zero(self):
        op = CrashAlwaysOperation(max_retries=0)
        op.run()
        assert op.status == OperationStatus.FAILED
        assert op.attempt == 0


class TestCancellation:
    def test_cancel_before_run(self):
        op = SuccessOperation()
        op.cancel()
        op.run()
        assert op.status == OperationStatus.CANCELLED

    def test_cancel_during_run(self):
        call_count = 0

        class SlowOperation(AbstractOperation[str]):
            def execute(self):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    time.sleep(0.05)
                return OperationResult(success=True, data="ok")

        op = SlowOperation(max_retries=3)
        op.cancel()
        op.run()
        assert op.status == OperationStatus.CANCELLED

    def test_cancel_requested_property(self):
        op = SuccessOperation()
        assert op.cancel_requested is False
        op.cancel()
        assert op.cancel_requested is True


class TestIsNonRetriable:
    def test_permission_error(self):
        assert AbstractOperation._is_non_retriable(PermissionError()) is True

    def test_file_not_found(self):
        assert AbstractOperation._is_non_retriable(FileNotFoundError()) is True

    def test_file_exists(self):
        assert AbstractOperation._is_non_retriable(FileExistsError()) is True

    def test_not_a_directory(self):
        assert AbstractOperation._is_non_retriable(NotADirectoryError()) is True

    def test_is_a_directory(self):
        assert AbstractOperation._is_non_retriable(IsADirectoryError()) is True

    def test_runtime_error_not_non_retriable(self):
        assert AbstractOperation._is_non_retriable(RuntimeError()) is False

    def test_value_error_not_non_retriable(self):
        assert AbstractOperation._is_non_retriable(ValueError()) is False


class TestShouldRetry:
    def test_retriable_exception(self):
        op = SuccessOperation()
        assert op.should_retry(RuntimeError()) is True

    def test_non_retriable_exception(self):
        op = SuccessOperation()
        assert op.should_retry(PermissionError()) is False


class TestBackoffDelay:
    def test_base_delay(self):
        op = SuccessOperation()
        op.attempt = 0
        delay = op.backoff_delay()
        assert 0.5 <= delay <= 0.7

    def test_exponential_growth(self):
        op = SuccessOperation()
        delays = []
        for attempt in range(4):
            op.attempt = attempt
            delays.append(op.backoff_delay())
        assert delays[0] < delays[1] < delays[2] < delays[3]


class TestProgress:
    def test_set_progress(self):
        op = SuccessOperation()
        op.set_progress(0.5, "halfway")
        assert op.progress == 0.5
        assert op.progress_message == "halfway"

    def test_set_progress_no_message(self):
        op = SuccessOperation()
        op.set_progress(0.75)
        assert op.progress == 0.75
        assert op.progress_message == ""


class TestIsFinished:
    def test_not_finished_initially(self):
        op = SuccessOperation()
        assert op.is_finished() is False

    def test_finished_on_success(self):
        op = SuccessOperation()
        op.run()
        assert op.is_finished() is True

    def test_finished_on_failure(self):
        op = FailOperation()
        op.run()
        assert op.is_finished() is True
