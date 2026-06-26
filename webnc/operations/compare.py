from __future__ import annotations

import fnmatch
from datetime import datetime
from pathlib import Path

from webnc.logging_config import logger
from webnc.operations.base import AbstractOperation, OperationResult
from webnc.vfs.paths import safe_path, relative_path


def _scan(dir_path: Path):
    result = {}
    base = relative_path(dir_path)
    try:
        for entry in dir_path.iterdir():
            try:
                st = entry.stat()
                result[entry.name] = {
                    "name": entry.name,
                    "path": f"{base}/{entry.name}",
                    "is_dir": entry.is_dir(),
                    "size": st.st_size if not entry.is_dir() else 0,
                    "modified_ts": st.st_mtime,
                    "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
                }
            except OSError:
                logger.warning("compare: skip unreadable entry %s", entry)
                continue
    except OSError:
        logger.warning("compare: iterdir failed for %s", dir_path)
    return result


class CompareOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "compare"
    def __init__(self, left: str, right: str, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.right = right

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        return True

    def execute(self) -> OperationResult[dict]:
        left_path = safe_path(self.left)
        right_path = safe_path(self.right)

        if not left_path.is_dir():
            return OperationResult(success=False, error_message=f"Left path is not a directory: {self.left}")
        if not right_path.is_dir():
            return OperationResult(success=False, error_message=f"Right path is not a directory: {self.right}")

        left_files = _scan(left_path)
        right_files = _scan(right_path)
        all_names = set(left_files) | set(right_files)

        only_left = []
        only_right = []
        different = []
        same = []

        for name in sorted(all_names, key=str.lower):
            lf = left_files.get(name)
            rf = right_files.get(name)
            if lf and not rf:
                only_left.append(lf)
            elif rf and not lf:
                only_right.append(rf)
            elif lf and rf:
                if (
                    lf["is_dir"] != rf["is_dir"]
                    or (
                        not lf["is_dir"]
                        and not rf["is_dir"]
                        and (
                            lf["size"] != rf["size"]
                            or abs(lf["modified_ts"] - rf["modified_ts"]) > 1
                        )
                    )
                ):
                    different.append({"name": name, "left": lf, "right": rf})
                else:
                    same.append({"name": name, "left": lf, "right": rf})

        return OperationResult(success=True, data={
            "only_left": only_left,
            "only_right": only_right,
            "different": different,
            "same": same,
            "left_total": len(only_left) + len(different) + len(same),
            "right_total": len(only_right) + len(different) + len(same),
        })
