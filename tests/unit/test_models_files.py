"""Tests for webnc.models.files — Pydantic validators."""
import pytest
from pydantic import ValidationError

from webnc.models.files import (
    CopyMoveRequest,
    RenameRequest,
    MkdirRequest,
    DeleteRequest,
    BatchDeleteRequest,
    SearchRequest,
    EditRequest,
    LinkRequest,
    FileInfo,
    DirListing,
    OperationResult,
)


class TestCopyMoveRequest:
    def test_valid(self):
        r = CopyMoveRequest(src="/C/file.txt", dest="/D/file.txt")
        assert r.src == "/C/file.txt"

    def test_empty_src_raises(self):
        with pytest.raises(ValidationError, match="path must not be empty"):
            CopyMoveRequest(src="  ", dest="/D/file.txt")

    def test_empty_dest_raises(self):
        with pytest.raises(ValidationError, match="path must not be empty"):
            CopyMoveRequest(src="/C/file.txt", dest="  ")


class TestRenameRequest:
    def test_valid(self):
        r = RenameRequest(path="/C/old.txt", new_name="new.txt")
        assert r.new_name == "new.txt"

    def test_strips_whitespace(self):
        r = RenameRequest(path="/C/file.txt", new_name="  new.txt  ")
        assert r.new_name == "new.txt"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError, match="invalid filename"):
            RenameRequest(path="/C/file.txt", new_name="  ")

    def test_slash_in_name_raises(self):
        with pytest.raises(ValidationError, match="invalid filename"):
            RenameRequest(path="/C/file.txt", new_name="sub/file.txt")

    def test_backslash_in_name_raises(self):
        with pytest.raises(ValidationError, match="invalid filename"):
            RenameRequest(path="/C/file.txt", new_name="sub\\file.txt")


class TestMkdirRequest:
    def test_valid(self):
        r = MkdirRequest(path="/C/newdir")
        assert r.path == "/C/newdir"


class TestDeleteRequest:
    def test_default_not_recursive(self):
        r = DeleteRequest(path="/C/file.txt")
        assert r.recursive is False

    def test_recursive(self):
        r = DeleteRequest(path="/C/dir", recursive=True)
        assert r.recursive is True


class TestBatchDeleteRequest:
    def test_valid(self):
        r = BatchDeleteRequest(paths=["/C/a.txt", "/C/b.txt"])
        assert len(r.paths) == 2

    def test_empty_list(self):
        r = BatchDeleteRequest(paths=[])
        assert r.paths == []


class TestSearchRequest:
    def test_defaults(self):
        r = SearchRequest(pattern="*.py")
        assert r.path == "/"
        assert r.max_results == 100

    def test_custom(self):
        r = SearchRequest(path="/C/src", pattern="test_*.py", max_results=50)
        assert r.max_results == 50


class TestEditRequest:
    def test_valid(self):
        r = EditRequest(path="/C/file.txt", content="hello world")
        assert r.content == "hello world"


class TestLinkRequest:
    def test_valid(self):
        r = LinkRequest(target="/C/original", link_path="/C/link")
        assert r.target == "/C/original"


class TestFileInfo:
    def test_valid(self):
        fi = FileInfo(
            name="test.txt",
            path="/C/test.txt",
            is_dir=False,
            size=1234,
            modified="2024-01-01T00:00:00",
            modified_ts=1704067200.0,
            permissions="r--r--r--",
            extension=".txt",
        )
        assert fi.name == "test.txt"
        assert fi.is_symlink is False

    def test_optional_owner(self):
        fi = FileInfo(
            name="f.txt",
            path="/C/f.txt",
            is_dir=False,
            size=10,
            modified="2024-01-01",
            modified_ts=0,
            permissions="r--r--r--",
            extension=".txt",
        )
        assert fi.owner is None


class TestDirListing:
    def test_valid(self):
        dl = DirListing(
            path="/C/src",
            parent="/C",
            items=[],
            total_files=5,
            total_dirs=2,
            total_size=1024,
        )
        assert dl.total_files == 5


class TestOperationResultModel:
    def test_success(self):
        r = OperationResult(success=True, message="done")
        assert r.path is None

    def test_with_path(self):
        r = OperationResult(success=True, message="ok", path="/C/file.txt")
        assert r.path == "/C/file.txt"
