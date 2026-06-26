"""Tests for webnc.operations.compare and syncop — scan, compare, sync."""
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from webnc.operations.compare import _scan, CompareOperation
from webnc.operations.syncop import _compare_content, SyncPlanOperation
from webnc.operations.base import OperationStatus
from webnc.vfs.paths import relative_path


def _to_url(p: Path) -> str:
    """Convert a Windows Path to URL-style path like /C/Users/..."""
    return relative_path(p)


@pytest.fixture
def sample_dirs(tmp_path):
    """Create two directories with test files."""
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()

    (left / "file1.txt").write_text("hello")
    (left / "file2.txt").write_text("world")
    (left / "subdir").mkdir()
    (left / "subdir" / "nested.txt").write_text("nested")

    (right / "file1.txt").write_text("hello")
    (right / "file3.txt").write_text("unique")
    (right / "subdir").mkdir()
    (right / "subdir" / "nested.txt").write_text("nested_diff")

    return left, right


class TestScan:
    def test_scan_returns_dict(self, tmp_path):
        result = _scan(tmp_path)
        assert isinstance(result, dict)

    def test_scan_finds_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        result = _scan(tmp_path)
        assert "a.txt" in result
        assert "b.txt" in result

    def test_scan_marks_directories(self, tmp_path):
        (tmp_path / "mydir").mkdir()
        result = _scan(tmp_path)
        assert result["mydir"]["is_dir"] is True
        assert result["mydir"]["size"] == 0

    def test_scan_skips_unreadable(self, tmp_path):
        result = _scan(tmp_path)
        assert isinstance(result, dict)

    def test_scan_entry_fields(self, tmp_path):
        (tmp_path / "test.txt").write_text("content")
        result = _scan(tmp_path)
        entry = result["test.txt"]
        assert "name" in entry
        assert "path" in entry
        assert "size" in entry
        assert "modified_ts" in entry
        assert "modified" in entry


class TestCompareOperation:
    def test_same_directories(self, tmp_path):
        left = tmp_path / "a"
        right = tmp_path / "b"
        left.mkdir()
        right.mkdir()
        (left / "f.txt").write_text("x")
        (right / "f.txt").write_text("x")

        op = CompareOperation(
            left=_to_url(left),
            right=_to_url(right),
            max_retries=0,
        )
        op.run()
        assert op.status == OperationStatus.SUCCESS
        data = op.result.data
        assert len(data["only_left"]) == 0
        assert len(data["only_right"]) == 0
        assert len(data["different"]) == 0
        assert len(data["same"]) == 1

    def test_files_only_left(self, sample_dirs):
        left, right = sample_dirs
        op = CompareOperation(left=_to_url(left), right=_to_url(right), max_retries=0)
        op.run()
        data = op.result.data
        left_names = [f["name"] for f in data["only_left"]]
        assert "file2.txt" in left_names

    def test_files_only_right(self, sample_dirs):
        left, right = sample_dirs
        op = CompareOperation(left=_to_url(left), right=_to_url(right), max_retries=0)
        op.run()
        data = op.result.data
        right_names = [f["name"] for f in data["only_right"]]
        assert "file3.txt" in right_names

    def test_different_files(self, sample_dirs):
        left, right = sample_dirs
        op = CompareOperation(left=_to_url(left), right=_to_url(right), max_retries=0)
        op.run()
        data = op.result.data
        # file1.txt exists in both with same content -> same
        # subdir exists in both as dirs -> same
        # file2.txt only in left, file3.txt only in right
        assert len(data["same"]) == 2
        assert len(data["only_left"]) == 1
        assert len(data["only_right"]) == 1

    def test_different_sizes_detected(self, tmp_path):
        left = tmp_path / "l"
        right = tmp_path / "r"
        left.mkdir()
        right.mkdir()
        (left / "shared.txt").write_text("short")
        (right / "shared.txt").write_text("much longer content")

        op = CompareOperation(left=_to_url(left), right=_to_url(right), max_retries=0)
        op.run()
        data = op.result.data
        assert len(data["different"]) == 1
        assert data["different"][0]["name"] == "shared.txt"

    def test_nonexistent_left(self, tmp_path):
        op = CompareOperation(
            left=_to_url(tmp_path / "nonexistent"),
            right=_to_url(tmp_path),
            max_retries=0,
        )
        op.run()
        assert op.status == OperationStatus.FAILED
        assert "not a directory" in op.result.error_message.lower()


class TestCompareContent:
    def test_identical_files(self, tmp_path):
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"same content")
        f2.write_bytes(b"same content")
        assert _compare_content(f1, f2) is True

    def test_different_files(self, tmp_path):
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"content1")
        f2.write_bytes(b"content2")
        assert _compare_content(f1, f2) is False

    def test_nonexistent_file(self, tmp_path):
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "nonexistent.bin"
        f1.write_bytes(b"data")
        assert _compare_content(f1, f2) is False


class TestSyncPlanOperation:
    def test_generates_plan(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "only_left.txt").write_text("a")
        (right / "only_right.txt").write_text("b")

        op = SyncPlanOperation(
            left=_to_url(left),
            right=_to_url(right),
            max_retries=0,
        )
        op.run()
        assert op.status == OperationStatus.SUCCESS
        data = op.result.data
        statuses = {item["status"] for item in data}
        assert "only_left" in statuses
        assert "only_right" in statuses

    def test_same_dirs_gives_same_status(self, tmp_path):
        left = tmp_path / "l"
        right = tmp_path / "r"
        left.mkdir()
        right.mkdir()
        (left / "f.txt").write_text("same")
        (right / "f.txt").write_text("same")

        op = SyncPlanOperation(
            left=_to_url(left),
            right=_to_url(right),
            max_retries=0,
        )
        op.run()
        data = op.result.data
        assert all(item["status"] == "same" for item in data)

    def test_asymmetric_mode(self, tmp_path):
        left = tmp_path / "l"
        right = tmp_path / "r"
        left.mkdir()
        right.mkdir()
        (right / "extra.txt").write_text("x")

        op = SyncPlanOperation(
            left=_to_url(left),
            right=_to_url(right),
            asymmetric=True,
            max_retries=0,
        )
        op.run()
        data = op.result.data
        only_right = [d for d in data if d["status"] == "only_right"]
        assert len(only_right) == 1
        assert only_right[0]["suggested"] == "delete_right"

    def test_filter_pattern(self, tmp_path):
        left = tmp_path / "l"
        right = tmp_path / "r"
        left.mkdir()
        right.mkdir()
        (left / "a.py").write_text("py")
        (left / "b.txt").write_text("txt")

        op = SyncPlanOperation(
            left=_to_url(left),
            right=_to_url(right),
            filter="*.py",
            max_retries=0,
        )
        op.run()
        data = op.result.data
        names = {item["name"] for item in data}
        assert "a.py" in names
        assert "b.txt" not in names
