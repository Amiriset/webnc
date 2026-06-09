"""Tests for /api/operation/{id} polling and cancel endpoints."""
import uuid

from webnc.operations.base import AbstractOperation, OperationResult, OperationStatus


class DummyOp(AbstractOperation[str]):
    def execute(self):
        return OperationResult(success=True, data="done")


class TestOperationPolling:
    def test_get_operation_found(self, mock_client, mock_operation_queue):
        op = DummyOp()
        op.status = OperationStatus.SUCCESS
        op.result = OperationResult(success=True, data="done")
        mock_operation_queue.get_operation.return_value = op

        r = mock_client.get(f"/api/operation/{op.operation_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "SUCCESS"
        assert data["result"]["success"] is True
        assert data["result"]["data"] == "done"

    def test_get_operation_not_found(self, mock_client, mock_operation_queue):
        mock_operation_queue.get_operation.return_value = None
        r = mock_client.get(f"/api/operation/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_get_operation_running(self, mock_client, mock_operation_queue):
        op = DummyOp()
        op.status = OperationStatus.RUNNING
        op.progress = 0.42
        op.progress_message = "working..."
        mock_operation_queue.get_operation.return_value = op

        r = mock_client.get(f"/api/operation/{op.operation_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "RUNNING"
        assert data["progress"] == 0.42
        assert data["progress_message"] == "working..."


class TestOperationCancel:
    def test_cancel_success(self, mock_client, mock_operation_queue):
        op_id = str(uuid.uuid4())
        mock_operation_queue.cancel_operation.return_value = True
        r = mock_client.post(f"/api/operation/{op_id}/cancel")
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    def test_cancel_not_found(self, mock_client, mock_operation_queue):
        mock_operation_queue.cancel_operation.return_value = False
        r = mock_client.post(f"/api/operation/{uuid.uuid4()}/cancel")
        assert r.status_code == 404
