from __future__ import annotations

import ctypes
import shutil

from webnc.logging_config import logger
from webnc.operations.base import AbstractOperation, OperationResult
from webnc.vfs.paths import DRIVE_LETTERS, safe_path, relative_path


class ListDrivesOperation(AbstractOperation[list]):
    def execute(self) -> OperationResult[list]:
        drives = []
        for letter in DRIVE_LETTERS:
            root = f"{letter}:\\"
            try:
                usage = shutil.disk_usage(root)
                label = self._get_volume_label(root)
                drives.append({
                    "drive": f"{letter}:",
                    "label": label or f"{letter}:",
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent_used": round(usage.used / usage.total * 100, 1),
                })
            except OSError:
                drives.append({
                    "drive": f"{letter}:", "label": f"{letter}:",
                    "total": 0, "used": 0, "free": 0, "percent_used": 0,
                })
        return OperationResult(success=True, data=drives)

    @staticmethod
    def _get_volume_label(root: str) -> str:
        try:
            buf = ctypes.create_unicode_buffer(261)
            ctypes.windll.kernel32.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0)
            return buf.value or ""
        except Exception:
            return ""


class DiskUsageOperation(AbstractOperation[dict]):
    def __init__(self, path: str = "/C/", **kwargs):
        super().__init__(**kwargs)
        self.path = path

    def execute(self) -> OperationResult[dict]:
        target = safe_path(self.path)
        try:
            usage = shutil.disk_usage(target)
        except OSError:
            return OperationResult(success=False, error_message=f"Cannot get disk usage for: {self.path}")
        return OperationResult(success=True, data={
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent_used": round(usage.used / usage.total * 100, 1),
            "path": relative_path(target),
        })
