"""Tests for /api/health and /api/config endpoints."""
from unittest.mock import MagicMock


class TestHealthEndpoint:
    def test_health_no_auth_required(self, mock_operation_queue, mock_file_service, mock_config_manager):
        """Health endpoint is exempted from auth."""
        import webnc.main as main_mod
        from webnc.security._state import set_auth_provider

        set_auth_provider(None)
        orig_q = main_mod.operation_queue
        main_mod.operation_queue = mock_operation_queue
        try:
            with TestClient(main_mod.app, raise_server_exceptions=False) as c:
                r = c.get("/api/health")
                assert r.status_code == 200
                data = r.json()
                assert "status" in data
                assert "version" in data
        finally:
            main_mod.operation_queue = orig_q
            set_auth_provider(MockAuthProvider())

    def test_health_returns_version(self, mock_client):
        from webnc.version import VERSION
        r = mock_client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["version"] == VERSION

    def test_health_returns_state(self, mock_client):
        r = mock_client.get("/api/health")
        assert r.status_code == 200
        assert "state" in r.json()


from fastapi.testclient import TestClient


class TestConfigEndpoint:
    def test_get_config(self, mock_client):
        r = mock_client.get("/api/config")
        assert r.status_code == 200
        data = r.json()
        assert "operations" in data
        assert "exec" in data

    def test_put_config(self, mock_client):
        new_data = {"custom": True, "operations": {}}
        r = mock_client.put("/api/config", json=new_data)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class MockAuthProvider:
    async def authenticate(self, request):
        from webnc.models.auth import UserInfo
        return UserInfo(username="admin", roles=["admin"])
