from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "config.json"

OPERATION_DEFAULTS = {
    "copy": {"max_retries": 3, "timeout": 600, "interval": 500},
    "move": {"max_retries": 3, "timeout": 600, "interval": 500},
    "batch_delete": {"max_retries": 2, "timeout": 120, "interval": 300},
    "search": {"max_retries": 2, "timeout": 120, "interval": 300},
    "compare": {"max_retries": 2, "timeout": 120, "interval": 300},
    "sync_plan": {"max_retries": 2, "timeout": 120, "interval": 300},
    "sync_execute": {"max_retries": 2, "timeout": 300, "interval": 500},
    "archive_list": {"max_retries": 1, "timeout": 30, "interval": 300},
}

EXEC_DEFAULTS = {
    "allowed_commands": [],
    "denied_commands": ["format", "diskpart", "shutdown", "reg", "reg.exe"],
    "timeout": 30,
}

EDITOR_DEFAULTS = {
    "max_edit_size": 1048576,
}

ASSOCIATIONS_DEFAULTS = {
    ".py": "edit",
    ".js": "edit",
    ".ts": "edit",
    ".html": "edit",
    ".css": "edit",
    ".json": "edit",
    ".md": "view",
    ".txt": "view",
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".tgz": "archive",
    ".7z": "archive",
    ".rar": "archive",
    ".jpg": "preview",
    ".png": "preview",
    ".gif": "preview",
}

KEYBINDING_DEFAULTS = {
    "F1": "help",
    "F2": "menu_left",
    "F3": "view",
    "F4": "edit",
    "F5": "copy",
    "F6": "move",
    "F7": "mkdir",
    "F8": "delete",
    "F9": "search",
    "F10": "quit",
    "F11": "fullscreen",
    "Enter": "navigate",
    "Tab": "switch_panel",
    "Insert": "select",
    "+": "select_group",
    "-": "deselect_group",
    "*": "invert_selection",
    "Backspace": "go_up",
    "ArrowUp": "up",
    "ArrowDown": "down",
    "Home": "home",
    "End": "end",
    "PageUp": "page_up",
    "PageDown": "page_down",
}


class ConfigManager:
    def __init__(self, path: str | Path = CONFIG_FILE):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        self._merge_defaults()

    def _merge_defaults(self) -> None:
        ops = self._data.setdefault("operations", {})
        for name, defaults in OPERATION_DEFAULTS.items():
            cfg = ops.setdefault(name, {})
            for k, v in defaults.items():
                cfg.setdefault(k, v)
        bindings = self._data.setdefault("keybindings", {})
        for k, v in KEYBINDING_DEFAULTS.items():
            bindings.setdefault(k, v)
        exec_cfg = self._data.setdefault("exec", {})
        for k, v in EXEC_DEFAULTS.items():
            exec_cfg.setdefault(k, v)
        editor_cfg = self._data.setdefault("editor", {})
        for k, v in EDITOR_DEFAULTS.items():
            editor_cfg.setdefault(k, v)
        assoc = self._data.setdefault("associations", {})
        for k, v in ASSOCIATIONS_DEFAULTS.items():
            assoc.setdefault(k, v)
        self.save()

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            tmp.replace(self.path)

    def get_raw(self) -> dict:
        return self._data

    def set_raw(self, data: dict) -> None:
        with self._lock:
            self._data = data
        self.save()

    def get_operation_config(self, name: str) -> dict:
        with self._lock:
            return dict(self._data.get("operations", {}).get(name, {}))

    def get_max_retries(self, op_name: str) -> int:
        return self.get_operation_config(op_name).get("max_retries", 3)

    def get_poll_timeout(self, op_name: str) -> int:
        return self.get_operation_config(op_name).get("timeout", 120)

    def get_poll_interval(self, op_name: str) -> int:
        return self.get_operation_config(op_name).get("interval", 300)

    def get_exec_allowed(self) -> list[str]:
        with self._lock:
            return list(self._data.get("exec", {}).get("allowed_commands", []))

    def get_exec_denied(self) -> list[str]:
        with self._lock:
            return list(self._data.get("exec", {}).get("denied_commands", []))

    def get_exec_timeout(self) -> int:
        with self._lock:
            return self._data.get("exec", {}).get("timeout", 30)

    def get_max_edit_size(self) -> int:
        with self._lock:
            return self._data.get("editor", {}).get("max_edit_size", 1048576)

    def get_associations(self) -> dict[str, str]:
        with self._lock:
            return dict(self._data.get("associations", {}))
