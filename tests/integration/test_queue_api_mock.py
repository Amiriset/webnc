"""Tests for queue-based API endpoints via mock OperationQueue."""
import uuid
from unittest.mock import MagicMock


def _fake_op_id():
    return str(uuid.uuid4())


class TestCopyEndpoint:
    def test_copy_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/copy", json={
            "src": "/C/a.txt", "dest": "/D/b.txt"
        })
        assert r.status_code == 200
        data = r.json()
        assert "operation_id" in data
        assert data["status"] == "QUEUED"
        assert "poll" in data
        mock_operation_queue.add_operation.assert_called_once()


class TestMoveEndpoint:
    def test_move_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/move", json={
            "src": "/C/a.txt", "dest": "/D/b.txt"
        })
        assert r.status_code == 200
        assert "operation_id" in r.json()
        assert r.json()["status"] == "QUEUED"


class TestBatchDeleteEndpoint:
    def test_batch_delete_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/batch-delete", json={
            "paths": ["/C/a.txt", "/C/b.txt"], "recursive": False
        })
        assert r.status_code == 200
        assert "operation_id" in r.json()


class TestSearchEndpoint:
    def test_search_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/search", json={
            "path": "/C/src", "pattern": "*.py", "max_results": 50
        })
        assert r.status_code == 200
        assert "operation_id" in r.json()


class TestCompareEndpoint:
    def test_compare_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/compare", json={
            "left": "/C/dir1", "right": "/C/dir2"
        })
        assert r.status_code == 200
        assert "operation_id" in r.json()


class TestSyncPlanEndpoint:
    def test_sync_plan_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/sync/plan", json={
            "left": "/C/a", "right": "/C/b",
            "subdirs": True, "by_content": False,
            "ignore_date": False, "asymmetric": False, "filter": "*"
        })
        assert r.status_code == 200
        assert "operation_id" in r.json()


class TestSyncExecuteEndpoint:
    def test_sync_execute_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.post("/api/sync/execute", json={
            "left": "/C/a", "right": "/C/b",
            "actions": [{"name": "file.txt", "action": "copy_left_to_right"}]
        })
        assert r.status_code == 200
        assert "operation_id" in r.json()


class TestArchiveListEndpoint:
    def test_archive_list_returns_operation_id(self, mock_client, mock_operation_queue):
        mock_operation_queue.add_operation.return_value = _fake_op_id()
        r = mock_client.get("/api/archive/list?path=/C/archive.zip")
        assert r.status_code == 200
        assert "operation_id" in r.json()
