from __future__ import annotations

from webnc.logging_config import logger
from webnc.operations.base import AbstractOperation, OperationResult


class CopyOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "copy"

    def __init__(self, src: str, dest: str, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    def should_retry(self, exception: Exception) -> bool:
        return not self._is_non_retriable(exception)

    def execute(self) -> OperationResult[dict]:
        from webnc.main import file_service
        result = file_service.copy(self.src, self.dest)
        if result["success"]:
            self.set_progress(1.0, "Done")
            return OperationResult(success=True, data={"path": result["path"]})
        return OperationResult(success=False, error_message=result.get("error", "Unknown error"))


class MoveOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "move"

    def __init__(self, src: str, dest: str, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    def should_retry(self, exception: Exception) -> bool:
        return not self._is_non_retriable(exception)

    def execute(self) -> OperationResult[dict]:
        from webnc.main import file_service
        result = file_service.move(self.src, self.dest)
        if result["success"]:
            return OperationResult(success=True, data={"path": result["path"]})
        return OperationResult(success=False, error_message=result.get("error", "Unknown error"))


class BatchDeleteOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "batch_delete"

    def __init__(self, paths: list[str], recursive: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.paths = paths
        self.recursive = recursive

    def should_retry(self, exception: Exception) -> bool:
        return not self._is_non_retriable(exception)

    def execute(self) -> OperationResult[dict]:
        from webnc.main import file_service
        result = file_service.batch_delete(self.paths, self.recursive)
        return OperationResult(
            success=result["success"],
            data={"message": result.get("message", ""), "deleted": result.get("deleted", []), "errors": result.get("errors", [])},
        )


class SearchOperation(AbstractOperation[list]):
    should_run_in_queue = True
    op_config_key = "search"

    def __init__(self, path: str, pattern: str, max_results: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.pattern = pattern
        self.max_results = max_results

    def execute(self) -> OperationResult[list]:
        from webnc.main import file_service
        result = file_service.search(self.path, self.pattern, self.max_results)
        if result["success"]:
            return OperationResult(success=True, data={"results": result["results"], "truncated": result["truncated"]})
        return OperationResult(success=False, error_message=result.get("error", "Unknown error"))
