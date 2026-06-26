from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from webnc.logging_config import logger
from webnc.operations.base import AbstractOperation, OperationResult
from webnc.vfs.paths import safe_path


class ArchiveListOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "archive_list"
    def __init__(self, path: str, password: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.password = password

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        type_name = type(exception).__name__
        if type_name in ("BadZipFile", "ReadError", "PasswordRequiredException", "ExtractError"):
            return False
        return True

    def execute(self) -> OperationResult[dict]:
        target = safe_path(self.path)

        if not target.exists():
            return OperationResult(success=False, error_message=f"Archive not found: {self.path}")
        if not target.is_file():
            return OperationResult(success=False, error_message="Not a file")

        ext = target.suffix.lower()
        stem = target.stem.lower()
        is_tar = ext in (".tar", ".gz", ".tgz", ".bz2", ".tbz2", ".xz") or any(
            stem.endswith(s) for s in (".tar", ".tar.gz", ".tar.bz2", ".tar.xz")
        )

        items = []

        if ext == ".zip":
            import zipfile

            with zipfile.ZipFile(target, "r") as zf:
                if self.password:
                    zf.setpassword(self.password.encode("utf-8"))
                for zi in zf.infolist():
                    name = zi.filename.rstrip("/")
                    if not name:
                        continue
                    parts = name.split("/")
                    is_dir = zi.filename.endswith("/")
                    items.append({
                        "name": parts[-1], "path": name,
                        "is_dir": is_dir, "size": 0 if is_dir else zi.file_size,
                        "modified": datetime(*zi.date_time).isoformat() if zi.date_time else "",
                        "extension": parts[-1].split(".")[-1].lower() if "." in parts[-1] and not is_dir else "",
                        "compressed": zi.compress_size,
                    })
        elif is_tar:
            import tarfile

            with tarfile.open(target, "r:*") as tf:
                for ti in tf.getmembers():
                    name = ti.name.rstrip("/")
                    if not name:
                        continue
                    parts = name.split("/")
                    is_dir = ti.isdir()
                    items.append({
                        "name": parts[-1], "path": name,
                        "is_dir": is_dir, "size": 0 if is_dir else ti.size,
                        "modified": datetime.fromtimestamp(ti.mtime).isoformat() if ti.mtime else "",
                        "extension": parts[-1].split(".")[-1].lower() if "." in parts[-1] and not is_dir else "",
                        "compressed": 0,
                    })
        else:
            return OperationResult(success=False, error_message=f"Unsupported archive format: {ext}")

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        parent_url = "/" + str(target.drive)[0] + str(target.parent).replace("\\", "/")[2:]
        if parent_url != self.path.rstrip("/"):
            items.insert(0, {"name": "..", "path": parent_url, "is_dir": True,
                             "size": 0, "modified": "", "extension": "", "_isParent": True})

        return OperationResult(success=True, data={"items": items, "total": len(items), "name": target.name})
