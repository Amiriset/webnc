from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

from webnc.logging_config import logger
from webnc.operations.base import AbstractOperation, OperationResult
from webnc.vfs.paths import safe_path


def _compare_content(left_path: Path, right_path: Path) -> bool:
    try:
        CHUNK = 65536
        with open(left_path, "rb") as lf, open(right_path, "rb") as rf:
            while True:
                lb = lf.read(CHUNK)
                rb = rf.read(CHUNK)
                if lb != rb:
                    return False
                if not lb:
                    return True
    except OSError:
        return False


class SyncPlanOperation(AbstractOperation[list]):
    should_run_in_queue = True
    op_config_key = "sync_plan"
    def __init__(self, left: str, right: str, subdirs: bool = True, by_content: bool = False,
                 ignore_date: bool = False, asymmetric: bool = False, filter: str = "*", **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.right = right
        self.subdirs = subdirs
        self.by_content = by_content
        self.ignore_date = ignore_date
        self.asymmetric = asymmetric
        self.filter = filter

    def execute(self) -> OperationResult[list]:
        left_path = safe_path(self.left)
        right_path = safe_path(self.right)

        if not left_path.is_dir() or not right_path.is_dir():
            return OperationResult(success=False, error_message="Both paths must be directories")

        def _walk(base: Path, prefix: str = ""):
            entries = {}
            try:
                for entry in sorted(base.iterdir(), key=lambda e: e.name.lower()):
                    rel = f"{prefix}/{entry.name}" if prefix else entry.name
                    if not fnmatch.fnmatch(entry.name, self.filter):
                        continue
                    try:
                        st = entry.stat()
                        entries[rel] = {
                            "name": entry.name,
                            "path": rel,
                            "is_dir": entry.is_dir(),
                            "size": 0 if entry.is_dir() else st.st_size,
                            "modified_ts": st.st_mtime,
                        }
                    except OSError:
                        continue
                    if entry.is_dir() and self.subdirs:
                        try:
                            sub = _walk(entry, rel)
                            entries.update(sub)
                        except OSError:
                            continue
            except OSError:
                pass
            return entries

        left_map = _walk(left_path)
        right_map = _walk(right_path)
        all_keys = set(left_map) | set(right_map)

        result = []
        for key in sorted(all_keys, key=str.lower):
            lf = left_map.get(key)
            rf = right_map.get(key)
            if lf and not rf:
                entry = {
                    **lf,
                    "left": {"size": lf["size"], "modified_ts": lf["modified_ts"]},
                    "right": None,
                }
                entry["suggested"] = "copy_left_to_right"
                entry["status"] = "only_left"
                result.append(entry)
            elif rf and not lf:
                entry = {
                    **rf,
                    "left": None,
                    "right": {"size": rf["size"], "modified_ts": rf["modified_ts"]},
                }
                entry["suggested"] = "delete_right" if self.asymmetric else "copy_right_to_left"
                entry["status"] = "only_right"
                result.append(entry)
            elif lf and rf:
                different = False
                if lf["is_dir"] != rf["is_dir"]:
                    different = True
                elif not lf["is_dir"] and not rf["is_dir"]:
                    if self.ignore_date:
                        different = lf["size"] != rf["size"]
                    else:
                        different = (
                            lf["size"] != rf["size"]
                            or abs(lf["modified_ts"] - rf["modified_ts"]) > 1
                        )
                    if not different and self.by_content:
                        different = not _compare_content(left_path / key, right_path / key)

                if different:
                    result.append({
                        "name": lf["name"], "path": key, "is_dir": lf["is_dir"],
                        "status": "different",
                        "left": {"size": lf["size"], "modified_ts": lf["modified_ts"]},
                        "right": {"size": rf["size"], "modified_ts": rf["modified_ts"]},
                    })
                else:
                    result.append({
                        "name": lf["name"], "path": key, "is_dir": lf["is_dir"],
                        "status": "same",
                        "left": {"size": lf["size"], "modified_ts": lf["modified_ts"]},
                        "right": {"size": rf["size"], "modified_ts": rf["modified_ts"]},
                    })

        return OperationResult(success=True, data=result)


class SyncExecuteOperation(AbstractOperation[list]):
    should_run_in_queue = True
    op_config_key = "sync_execute"
    def __init__(self, left: str, right: str, actions: list, **kwargs):
        super().__init__(**kwargs)
        self.left = left
        self.right = right
        self.actions = actions

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        return True

    def execute(self) -> OperationResult[list]:
        left_path = safe_path(self.left)
        right_path = safe_path(self.right)
        results = []
        total = len(self.actions)

        for i, act in enumerate(self.actions):
            if self.cancel_requested:
                break
            self.set_progress(i / total, f"Processing {act.name}")

            src = right_path / act.name if act.action == "copy_right_to_left" else left_path / act.name
            dst = left_path / act.name if act.action == "copy_right_to_left" else right_path / act.name

            try:
                if act.action.startswith("copy"):
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                    results.append({"name": act.name, "action": act.action, "ok": True})
                elif act.action.startswith("delete"):
                    target = left_path / act.name if act.action == "delete_left" else right_path / act.name
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                    results.append({"name": act.name, "action": act.action, "ok": True})
            except Exception as e:
                results.append({"name": act.name, "action": act.action, "ok": False, "error": str(e)})

        return OperationResult(success=True, data=results)
