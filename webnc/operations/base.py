from __future__ import annotations

import random
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Generic, Optional, TypeVar

from webnc.logging_config import logger

TResult = TypeVar("TResult")


class OperationStatus(Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class OperationResult(Generic[TResult]):
    success: bool
    data: Optional[TResult] = None
    error_message: Optional[str] = None


@dataclass
class AbstractOperation(ABC, Generic[TResult]):
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: OperationStatus = OperationStatus.CREATED
    result: Optional[OperationResult[TResult]] = None
    max_retries: int = 3
    attempt: int = 0
    should_run_in_queue: ClassVar[bool] = False
    op_config_key: ClassVar[str] = ""
    progress: float = 0.0
    progress_message: str = ""
    _cancel_requested: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        if self.op_config_key:
            try:
                from webnc.main import config_manager
                cfg = config_manager.get_operation_config(self.op_config_key)
                if "max_retries" in cfg:
                    self.max_retries = int(cfg["max_retries"])
            except (ImportError, AttributeError):
                pass

    @abstractmethod
    def execute(self) -> OperationResult[TResult]:
        raise NotImplementedError

    @staticmethod
    def _is_non_retriable(exception: Exception) -> bool:
        return isinstance(exception, (
            PermissionError,
            FileNotFoundError,
            FileExistsError,
            NotADirectoryError,
            IsADirectoryError,
            BlockingIOError,
            InterruptedError,
        ))

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        return True

    def get_poll_config(self) -> dict:
        if self.op_config_key:
            try:
                from webnc.main import config_manager
                return config_manager.get_operation_config(self.op_config_key)
            except (ImportError, AttributeError):
                pass
        return {"timeout": 120, "interval": 300}

    def backoff_delay(self) -> float:
        base = 0.5
        delay = base * (2 ** self.attempt)
        jitter = random.uniform(0, 0.2 * delay)
        return delay + jitter

    def cancel(self) -> None:
        with self._lock:
            self._cancel_requested = True

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    def is_finished(self) -> bool:
        return self.status in (OperationStatus.SUCCESS, OperationStatus.FAILED, OperationStatus.CANCELLED)

    def set_progress(self, value: float, message: str = "") -> None:
        self.progress = value
        if message:
            self.progress_message = message

    def run(self) -> None:
        self.status = OperationStatus.RUNNING

        if self.cancel_requested:
            self.status = OperationStatus.CANCELLED
            self.result = OperationResult(success=False, error_message="Cancelled")
            return

        if self.max_retries == 0:
            try:
                self.result = self.execute()
            except Exception as e:
                self.result = OperationResult(success=False, error_message=str(e))
                self.status = OperationStatus.FAILED
                return
            self.status = OperationStatus.SUCCESS if self.result.success else OperationStatus.FAILED
            return

        while self.attempt <= self.max_retries:
            if self.cancel_requested:
                self.status = OperationStatus.CANCELLED
                self.result = OperationResult(success=False, error_message="Cancelled")
                return

            self.attempt += 1
            try:
                self.result = self.execute()
                if self.result.success:
                    self.status = OperationStatus.SUCCESS
                    return
                self.status = OperationStatus.FAILED
                return
            except Exception as e:
                if not self.should_retry(e) or self.attempt > self.max_retries:
                    self.result = OperationResult(success=False, error_message=str(e))
                    self.status = OperationStatus.FAILED
                    logger.exception("Operation %s failed after %d attempt(s): %s", self.operation_id, self.attempt, e)
                    return
                logger.warning("Operation %s attempt %d failed, retrying: %s", self.operation_id, self.attempt, e)
                time.sleep(self.backoff_delay())

        self.status = OperationStatus.FAILED
