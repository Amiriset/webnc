"""Tests for file operation endpoints via mock FileService."""
from unittest.mock import MagicMock


class TestListDirectory:
    def test_list_returns_dir_listing(self, mock_client, mock_file_service):
        mock_file_service.list_directory.return_value = {
            "success": True,
            "path": "/C/src",
            "parent": "/C",
            "items": [
                {"name": "a.txt", "path": "/C/src/a.txt", "is_dir": False,
                 "size": 100, "modified": "2024-01-01T00:00:00", "modified_ts": 0,
                 "permissions": "r--r--r--", "extension": ".txt"}
            ],
            "total_files": 1,
            "total_dirs": 0,
            "total_size": 100,
        }
        r = mock_client.get("/api/list?path=/C/src")
        assert r.status_code == 200
        data = r.json()
        assert data["path"] == "/C/src"
        assert len(data["items"]) == 1
        assert data["total_files"] == 1
        mock_file_service.list_directory.assert_called_once()

    def test_list_with_sort_params(self, mock_client, mock_file_service):
        mock_file_service.list_directory.return_value = {
            "success": True, "path": "/C/", "parent": None,
            "items": [], "total_files": 0, "total_dirs": 0, "total_size": 0,
        }
        r = mock_client.get("/api/list?path=/C/&sort_by=size&sort_dir=desc&show_hidden=true")
        assert r.status_code == 200
        mock_file_service.list_directory.assert_called_once_with(
            "/C/", "size", "desc", True, None
        )

    def test_list_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.list_directory.return_value = {
            "success": False, "error": "Path not found",
        }
        r = mock_client.get("/api/list?path=/nonexistent")
        assert r.status_code == 400


class TestViewFile:
    def test_view_returns_content(self, mock_client, mock_file_service):
        mock_file_service.read_file.return_value = {
            "success": True, "content": "hello world",
            "encoding": "utf-8", "path": "/C/test.txt",
        }
        r = mock_client.get("/api/view?path=/C/test.txt")
        assert r.status_code == 200
        assert r.json()["content"] == "hello world"

    def test_view_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.read_file.return_value = {
            "success": False, "error": "File not found",
        }
        r = mock_client.get("/api/view?path=/missing.txt")
        assert r.status_code == 400


class TestEditFile:
    def test_edit_saves_content(self, mock_client, mock_file_service):
        mock_file_service.write_file.return_value = {
            "success": True, "path": "/C/file.txt",
        }
        r = mock_client.post("/api/edit", json={
            "path": "/C/file.txt", "content": "new content"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        mock_file_service.write_file.assert_called_once_with(
            "/C/file.txt", "new content"
        )

    def test_edit_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.write_file.return_value = {
            "success": False, "error": "Permission denied",
        }
        r = mock_client.post("/api/edit", json={
            "path": "/C/readonly.txt", "content": "x"
        })
        assert r.status_code == 400


class TestRenameFile:
    def test_rename_calls_service(self, mock_client, mock_file_service):
        mock_file_service.rename.return_value = {
            "success": True, "path": "/C/new.txt",
        }
        r = mock_client.post("/api/rename", json={
            "path": "/C/old.txt", "new_name": "new.txt"
        })
        assert r.status_code == 200
        assert r.json()["success"] is True
        mock_file_service.rename.assert_called_once_with("/C/old.txt", "new.txt")

    def test_rename_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.rename.return_value = {
            "success": False, "error": "Name exists",
        }
        r = mock_client.post("/api/rename", json={
            "path": "/C/a.txt", "new_name": "b.txt"
        })
        assert r.status_code == 400


class TestMkdir:
    def test_mkdir_calls_service(self, mock_client, mock_file_service):
        mock_file_service.make_directory.return_value = {
            "success": True, "path": "/C/newdir",
        }
        r = mock_client.post("/api/mkdir", json={"path": "/C/newdir"})
        assert r.status_code == 200
        mock_file_service.make_directory.assert_called_once_with("/C/newdir")

    def test_mkdir_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.make_directory.return_value = {
            "success": False, "error": "Already exists",
        }
        r = mock_client.post("/api/mkdir", json={"path": "/C/existing"})
        assert r.status_code == 400


class TestDelete:
    def test_delete_calls_service(self, mock_client, mock_file_service):
        mock_file_service.delete.return_value = {"success": True}
        r = mock_client.post("/api/delete", json={
            "path": "/C/file.txt", "recursive": False
        })
        assert r.status_code == 200
        mock_file_service.delete.assert_called_once_with("/C/file.txt", False)

    def test_delete_recursive(self, mock_client, mock_file_service):
        mock_file_service.delete.return_value = {"success": True}
        r = mock_client.post("/api/delete", json={
            "path": "/C/dir", "recursive": True
        })
        assert r.status_code == 200
        mock_file_service.delete.assert_called_once_with("/C/dir", True)


class TestFileInfo:
    def test_info_returns_data(self, mock_client, mock_file_service):
        mock_file_service.file_info.return_value = {
            "success": True,
            "data": {"name": "file.txt", "size": 100},
        }
        r = mock_client.get("/api/info?path=/C/file.txt")
        assert r.status_code == 200
        assert r.json()["name"] == "file.txt"

    def test_info_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.file_info.return_value = {
            "success": False, "error": "Not found",
        }
        r = mock_client.get("/api/info?path=/missing")
        assert r.status_code == 400


class TestTree:
    def test_tree_returns_data(self, mock_client, mock_file_service):
        mock_file_service.tree.return_value = {
            "success": True, "name": "project",
            "dirs": [{"name": "src", "is_dir": True}],
            "files": [{"name": "readme.txt", "is_dir": False}],
        }
        r = mock_client.get("/api/tree?path=/C/project")
        assert r.status_code == 200
        assert "success" in r.json()

    def test_tree_error_returns_400(self, mock_client, mock_file_service):
        mock_file_service.tree.return_value = {
            "success": False, "error": "Not a directory",
        }
        r = mock_client.get("/api/tree?path=/C/file.txt")
        assert r.status_code == 400
