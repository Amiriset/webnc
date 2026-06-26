"""Tests for auth middleware — exemptions, 401, 200 with provider."""
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from webnc.models.auth import UserInfo
from webnc.security._state import set_auth_provider, get_auth_provider


class TestAuthExemptions:
    def test_health_no_auth(self, mock_file_service, mock_operation_queue, mock_config_manager):
        """Health is exempted — works without auth provider."""
        import webnc.main as main_mod
        orig = get_auth_provider()
        set_auth_provider(None)
        orig_q = main_mod.operation_queue
        main_mod.operation_queue = mock_operation_queue
        try:
            with TestClient(main_mod.app) as c:
                r = c.get("/api/health")
                assert r.status_code == 200
        finally:
            main_mod.operation_queue = orig_q
            set_auth_provider(orig)

    def test_drives_no_auth(self, mock_file_service, mock_operation_queue, mock_config_manager):
        """Drives is exempted — works without auth provider."""
        import webnc.main as main_mod
        orig = get_auth_provider()
        set_auth_provider(None)
        orig_q = main_mod.operation_queue
        main_mod.operation_queue = mock_operation_queue
        try:
            mock_operation_queue.run_sync = AsyncMock(return_value=[])
            with TestClient(main_mod.app) as c:
                r = c.get("/api/drives")
                assert r.status_code == 200
        finally:
            main_mod.operation_queue = orig_q
            set_auth_provider(orig)

    def test_disk_no_auth(self, mock_file_service, mock_operation_queue, mock_config_manager):
        """Disk is exempted — works without auth provider."""
        import webnc.main as main_mod
        orig = get_auth_provider()
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
            set_auth_provider(orig)


class TestAuthProtected:
    def test_list_no_auth_returns_401(self, mock_file_service, mock_operation_queue, mock_config_manager):
        import webnc.main as main_mod
        orig = get_auth_provider()
        set_auth_provider(None)
        try:
            with TestClient(main_mod.app) as c:
                r = c.get("/api/list?path=/C/")
                assert r.status_code == 401
        finally:
            set_auth_provider(orig)

    def test_config_no_auth_returns_401(self, mock_file_service, mock_operation_queue, mock_config_manager):
        import webnc.main as main_mod
        orig = get_auth_provider()
        set_auth_provider(None)
        try:
            with TestClient(main_mod.app) as c:
                r = c.get("/api/config")
                assert r.status_code == 401
        finally:
            set_auth_provider(orig)

    def test_list_with_auth_returns_200(self, mock_client):
        from unittest.mock import MagicMock
        import webnc.main as main_mod
        main_mod.file_service.list_directory = MagicMock(return_value={
            "success": True,
            "path": "/",
            "parent": None,
            "items": [],
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
        })
        r = mock_client.get("/api/list?path=/C/")
        assert r.status_code == 200
