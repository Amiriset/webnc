import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from webnc.models.auth import UserInfo
from webnc.security._state import set_auth_provider, get_auth_provider


class MockAuthProvider:
    """Always-authenticates provider for integration tests."""

    async def authenticate(self, request):
        return UserInfo(username="admin", roles=["admin"])


@pytest.fixture
def mock_auth():
    """Set and restore auth provider around a test."""
    original = get_auth_provider()
    set_auth_provider(MockAuthProvider())
    yield
    set_auth_provider(original)


@pytest.fixture
def no_auth():
    """Ensure no auth provider is set (401 for protected endpoints)."""
    original = get_auth_provider()
    set_auth_provider(None)
    yield
    set_auth_provider(original)


@pytest.fixture
def mock_file_service():
    return MagicMock()


@pytest.fixture
def mock_operation_queue():
    q = MagicMock()
    q.shutdown = MagicMock()
    return q


@pytest.fixture
def mock_config_manager():
    cm = MagicMock()
    cm.get_max_edit_size.return_value = 1048576
    cm.get_exec_allowed.return_value = []
    cm.get_exec_denied.return_value = ["format", "diskpart", "shutdown", "reg", "reg.exe"]
    cm.get_exec_timeout.return_value = 30
    cm.get_raw.return_value = {
        "operations": {"copy": {"max_retries": 3, "timeout": 600, "interval": 500}},
        "exec": {"allowed_commands": [], "denied_commands": ["format"], "timeout": 30},
        "editor": {"max_edit_size": 1048576},
        "keybindings": {},
        "associations": {},
    }
    return cm


@pytest.fixture
def mock_client(mock_auth, mock_file_service, mock_operation_queue, mock_config_manager):
    """TestClient with all dependencies mocked via globals patching."""
    import webnc.main as main_mod

    orig_fs = main_mod.file_service
    orig_q = main_mod.operation_queue
    orig_cm = main_mod.config_manager

    main_mod.file_service = mock_file_service
    main_mod.operation_queue = mock_operation_queue
    main_mod.config_manager = mock_config_manager

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        yield c

    main_mod.file_service = orig_fs
    main_mod.operation_queue = orig_q
    main_mod.config_manager = orig_cm


@pytest.fixture
def e2e_client(mock_auth):
    """TestClient with real WindowsFileService — for E2E tests on tmp_path."""
    import webnc.main as main_mod
    from webnc.services.windows_service import WindowsFileService
    from webnc.operations.queue import OperationQueue
    from webnc.config_manager import ConfigManager

    orig_fs = main_mod.file_service
    orig_q = main_mod.operation_queue
    orig_cm = main_mod.config_manager

    main_mod.file_service = WindowsFileService()
    main_mod.operation_queue = OperationQueue(max_workers=2)
    main_mod.config_manager = ConfigManager()

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        yield c

    main_mod.operation_queue.shutdown(wait=False)
    main_mod.file_service = orig_fs
    main_mod.operation_queue = orig_q
    main_mod.config_manager = orig_cm


def _to_url(p: Path) -> str:
    """Convert Windows Path to URL-style /C/Users/..."""
    from webnc.vfs.paths import relative_path
    return relative_path(p)
