"""Tests for /api/exec endpoint — allow/deny lists, timeout, validation."""
from unittest.mock import MagicMock, patch


class TestExecEndpoint:
    def test_empty_command_returns_400(self, mock_client):
        r = mock_client.post("/api/exec", json={"command": ""})
        assert r.status_code == 400

    def test_whitespace_command_returns_400(self, mock_client):
        r = mock_client.post("/api/exec", json={"command": "   "})
        assert r.status_code == 400

    def test_denied_command_returns_403(self, mock_client):
        r = mock_client.post("/api/exec", json={"command": "format C:"})
        assert r.status_code == 403
        assert "denied" in r.json()["detail"].lower()

    def test_allowed_command_executes(self, mock_client, mock_config_manager):
        mock_config_manager.get_exec_allowed.return_value = ["echo"]
        mock_config_manager.get_exec_denied.return_value = []
        r = mock_client.post("/api/exec", json={
            "command": "echo hello", "cwd": ""
        })
        assert r.status_code == 200
        data = r.json()
        assert "stdout" in data
        assert "returncode" in data
        assert data["returncode"] == 0

    def test_command_not_in_allowlist_returns_403(self, mock_client, mock_config_manager):
        mock_config_manager.get_exec_allowed.return_value = ["echo"]
        mock_config_manager.get_exec_denied.return_value = []
        r = mock_client.post("/api/exec", json={"command": "dir"})
        assert r.status_code == 403
        assert "not allowed" in r.json()["detail"].lower()

    def test_exec_uses_config_timeout(self, mock_client, mock_config_manager):
        mock_config_manager.get_exec_allowed.return_value = []
        mock_config_manager.get_exec_denied.return_value = ["format"]
        mock_config_manager.get_exec_timeout.return_value = 5
        r = mock_client.post("/api/exec", json={"command": "echo test"})
        assert r.status_code == 200
        mock_config_manager.get_exec_timeout.assert_called()
