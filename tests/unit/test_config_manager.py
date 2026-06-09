"""Tests for webnc.config_manager — ConfigManager."""
import json
import threading
from pathlib import Path

import pytest

from webnc.config_manager import (
    ConfigManager,
    OPERATION_DEFAULTS,
    EXEC_DEFAULTS,
    EDITOR_DEFAULTS,
    ASSOCIATIONS_DEFAULTS,
    KEYBINDING_DEFAULTS,
)


@pytest.fixture
def tmp_config(tmp_path):
    config_file = tmp_path / "config.json"
    return config_file


@pytest.fixture
def manager(tmp_config):
    return ConfigManager(path=tmp_config)


class TestConfigManagerInit:
    def test_creates_config_with_defaults(self, manager, tmp_config):
        assert tmp_config.exists()
        data = manager.get_raw()
        assert "operations" in data
        assert "exec" in data
        assert "editor" in data
        assert "keybindings" in data
        assert "associations" in data

    def test_loads_existing_config(self, tmp_config):
        existing = {
            "operations": {"copy": {"max_retries": 5}},
            "custom_key": "value",
        }
        tmp_config.write_text(json.dumps(existing), encoding="utf-8")
        manager = ConfigManager(path=tmp_config)
        data = manager.get_raw()
        assert data["operations"]["copy"]["max_retries"] == 5
        assert data["custom_key"] == "value"

    def test_defaults_not_overwritten(self, tmp_config):
        existing = {
            "operations": {"copy": {"max_retries": 10}},
        }
        tmp_config.write_text(json.dumps(existing), encoding="utf-8")
        manager = ConfigManager(path=tmp_config)
        cfg = manager.get_operation_config("copy")
        assert cfg["max_retries"] == 10
        assert cfg["timeout"] == OPERATION_DEFAULTS["copy"]["timeout"]

    def test_nonexistent_config_creates_empty(self, tmp_path):
        config_file = tmp_path / "nonexistent" / "config.json"
        manager = ConfigManager(path=config_file)
        assert config_file.exists()
        assert manager.get_raw()["operations"]["copy"]["max_retries"] == 3


class TestMergeDefaults:
    def test_operation_defaults_merged(self, manager):
        for name, defaults in OPERATION_DEFAULTS.items():
            cfg = manager.get_operation_config(name)
            for k, v in defaults.items():
                assert cfg[k] == v

    def test_exec_defaults_merged(self, manager):
        assert manager.get_exec_allowed() == EXEC_DEFAULTS["allowed_commands"]
        assert manager.get_exec_denied() == EXEC_DEFAULTS["denied_commands"]
        assert manager.get_exec_timeout() == EXEC_DEFAULTS["timeout"]

    def test_editor_defaults_merged(self, manager):
        assert manager.get_max_edit_size() == EDITOR_DEFAULTS["max_edit_size"]

    def test_keybinding_defaults_merged(self, manager):
        data = manager.get_raw()
        for k, v in KEYBINDING_DEFAULTS.items():
            assert data["keybindings"][k] == v

    def test_association_defaults_merged(self, manager):
        data = manager.get_raw()
        for k, v in ASSOCIATIONS_DEFAULTS.items():
            assert data["associations"][k] == v


class TestSaveLoad:
    def test_save_load_roundtrip(self, manager, tmp_config):
        manager.set_raw({"test": True, "operations": manager.get_raw()["operations"]})
        loaded = json.loads(tmp_config.read_text(encoding="utf-8"))
        assert loaded["test"] is True

    def test_atomic_write(self, manager, tmp_config):
        manager.save()
        assert tmp_config.with_suffix(".tmp").exists() is False or tmp_config.exists()


class TestGetters:
    def test_get_max_retries(self, manager):
        assert manager.get_max_retries("copy") == 3
        assert manager.get_max_retries("unknown_op") == 3

    def test_get_poll_timeout(self, manager):
        assert manager.get_poll_timeout("copy") == 600

    def test_get_poll_interval(self, manager):
        assert manager.get_poll_interval("copy") == 500

    def test_get_exec_denied(self, manager):
        denied = manager.get_exec_denied()
        assert "format" in denied
        assert "diskpart" in denied
        assert isinstance(denied, list)

    def test_get_associations(self, manager):
        assoc = manager.get_associations()
        assert assoc[".py"] == "edit"
        assert assoc[".md"] == "view"
        assert assoc[".zip"] == "archive"


class TestThreadSafety:
    def test_concurrent_reads(self, manager):
        results = []

        def read_config():
            for _ in range(100):
                results.append(manager.get_raw())

        threads = [threading.Thread(target=read_config) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 400

    def test_concurrent_writes(self, manager):
        def write_config(i):
            for _ in range(10):
                data = manager.get_raw()
                data["counter"] = i
                manager.set_raw(data)

        threads = [threading.Thread(target=write_config, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        final = manager.get_raw()
        assert "counter" in final
