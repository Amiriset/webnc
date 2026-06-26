"""Tests for sync execution endpoints: /api/sysinfo, /api/drives, /api/disk."""
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient


class TestSysinfoEndpoint:
    def test_sysinfo_returns_data(self, mock_client, mock_operation_queue):
        mock_operation_queue.run_sync = AsyncMock(return_value={
            "os": "Windows", "hostname": "test", "cpu": "x86_64",
            "ram_total": 16000000000, "ram_used": 8000000000,
        })
        r = mock_client.get("/api/sysinfo")
        assert r.status_code == 200
        data = r.json()
        assert "os" in data
        assert data["os"] == "Windows"


class TestDrivesEndpoint:
    def test_drives_no_auth_required(self, mock_file_service, mock_operation_queue, mock_config_manager):
        """Drives endpoint is exempted from auth."""
        import webnc.main as main_mod
        from webnc.security._state import set_auth_provider
        orig = set_auth_provider(None) or None

        orig_q = main_mod.operation_queue
        main_mod.operation_queue = mock_operation_queue
        try:
            mock_operation_queue.run_sync = AsyncMock(return_value=[
                {"letter": "C", "label": "System", "total": 500000000000, "free": 200000000000}
            ])
            with TestClient(main_mod.app) as c:
                r = c.get("/api/drives")
                assert r.status_code == 200
                assert isinstance(r.json(), list)
        finally:
            main_mod.operation_queue = orig_q
            from webnc.security._state import set_auth_provider as sap
            from webnc.security.console_token import ConsoleTokenProvider
            # Restore to no-auth state for subsequent tests
            sap(None)

    def test_drives_returns_list(self, mock_client, mock_operation_queue):
        mock_operation_queue.run_sync = AsyncMock(return_value=[])
        r = mock_client.get("/api/drives")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestDiskEndpoint:
    def test_disk_returns_usage(self, mock_client, mock_operation_queue):
        mock_operation_queue.run_sync = AsyncMock(return_value={
            "total": 500000000000,
            "used": 300000000000,
            "free": 200000000000,
        })
        r = mock_client.get("/api/disk?path=/C/")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "free" in data

    def test_disk_no_auth_required(self, mock_file_service, mock_operation_queue, mock_config_manager):
        """Disk endpoint is exempted from auth."""
        import webnc.main as main_mod
        from webnc.security._state import set_auth_provider

        set_auth_provider(None)
        orig_q = main_mod.operation_queue
        main_mod.operation_queue = mock_operation_queue
        try:
            mock_operation_queue.run_sync = AsyncMock(return_value={"total": 100})
            with TestClient(main_mod.app) as c:
                r = c.get("/api/disk?path=/C/")
                assert r.status_code == 200
        finally:
            main_mod.operation_queue = orig_q
            set_auth_provider(None)
