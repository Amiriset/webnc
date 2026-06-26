from __future__ import annotations

import ctypes
import os
import platform

from webnc.logging_config import logger
from webnc.operations.base import AbstractOperation, OperationResult
from webnc.operations.drives import ListDrivesOperation


class SystemInfoOperation(AbstractOperation[dict]):
    def execute(self) -> OperationResult[dict]:
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()

        uptime_seconds = 0
        try:
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            uptime_seconds = uptime_ms // 1000
        except Exception:
            pass

        ram_total = 0
        ram_avail = 0
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(mem)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                ram_total = mem.ullTotalPhys
                ram_avail = mem.ullAvailPhys
        except Exception:
            pass

        drives = ListDrivesOperation().execute()

        return OperationResult(success=True, data={
            "os": f"{os_name} {os_release} (build {os_version[:10]})",
            "hostname": platform.node(),
            "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", ""),
            "architecture": platform.machine(),
            "uptime": uptime_seconds,
            "ram_total": ram_total,
            "ram_used": ram_total - ram_avail,
            "ram_free": ram_avail,
            "drives": drives.data if drives.success else [],
        })
