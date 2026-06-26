"""Tests for webnc.security.nc_crypto — rate limit, recovery key, UUID formatting."""
import time
from unittest.mock import patch

import pytest

from webnc.security.nc_crypto import (
    _format_smbios_uuid,
    generate_recovery_key,
    check_rate_limit,
    register_failed_attempt,
    register_successful_attempt,
    LOGIN_TRACKER,
    _LOGIN_TRACKER_LOCK,
)


@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset global LOGIN_TRACKER between tests."""
    with _LOGIN_TRACKER_LOCK:
        LOGIN_TRACKER.clear()
    yield
    with _LOGIN_TRACKER_LOCK:
        LOGIN_TRACKER.clear()


class TestFormatSmbiosUuid:
    def test_known_bytes(self):
        b = bytes(range(16))
        result = _format_smbios_uuid(b)
        assert result == "03020100-0504-0706-0809-0A0B0C0D0E0F"

    def test_all_zeros(self):
        b = b'\x00' * 16
        result = _format_smbios_uuid(b)
        assert result == "00000000-0000-0000-0000-000000000000"

    def test_all_ff(self):
        b = b'\xff' * 16
        result = _format_smbios_uuid(b)
        assert result == "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"

    def test_format_length(self):
        b = b'\xaa' * 16
        result = _format_smbios_uuid(b)
        # 8-4-4-4-12 = 36 chars + 4 dashes = 36
        assert len(result) == 36
        assert result.count('-') == 4


class TestGenerateRecoveryKey:
    def test_format(self):
        key = generate_recovery_key()
        assert key.startswith("WNC3-")
        parts = key.split("-")
        assert parts[0] == "WNC3"
        # 20 bytes -> 32 base32 chars -> 8 groups of 4
        assert len(parts) == 9  # WNC3 + 8 groups

    def test_uniqueness(self):
        keys = {generate_recovery_key() for _ in range(100)}
        assert len(keys) == 100

    def test_alphanumeric_groups(self):
        key = generate_recovery_key()
        groups = key.split("-")[1:]
        for g in groups:
            assert len(g) == 4
            assert g.isalnum()


class TestRateLimit:
    def test_new_ip_allowed(self):
        assert check_rate_limit("10.0.0.1") is True

    def test_existing_ip_allowed(self):
        check_rate_limit("10.0.0.2")
        assert check_rate_limit("10.0.0.2") is True

    def test_lockout_after_5_failures(self):
        ip = "10.0.0.3"
        check_rate_limit(ip)
        for _ in range(5):
            register_failed_attempt(ip)
        assert check_rate_limit(ip) is False

    def test_lockout_cleared_after_timeout(self):
        ip = "10.0.0.4"
        check_rate_limit(ip)
        for _ in range(5):
            register_failed_attempt(ip)
        with _LOGIN_TRACKER_LOCK:
            LOGIN_TRACKER[ip]["locked_until"] = time.time() - 1
        assert check_rate_limit(ip) is True
        with _LOGIN_TRACKER_LOCK:
            assert LOGIN_TRACKER[ip]["attempts"] == 0

    def test_successful_attempt_resets(self):
        ip = "10.0.0.5"
        check_rate_limit(ip)
        for _ in range(3):
            register_failed_attempt(ip)
        register_successful_attempt(ip)
        with _LOGIN_TRACKER_LOCK:
            assert LOGIN_TRACKER[ip]["attempts"] == 0
        assert check_rate_limit(ip) is True

    def test_lockout_resets_counter(self):
        ip = "10.0.0.6"
        check_rate_limit(ip)
        for _ in range(5):
            register_failed_attempt(ip)
        # Lockout expired
        with _LOGIN_TRACKER_LOCK:
            LOGIN_TRACKER[ip]["locked_until"] = time.time() - 1
        check_rate_limit(ip)
        # Now fresh 5 attempts before lockout
        for _ in range(4):
            register_failed_attempt(ip)
        assert check_rate_limit(ip) is True
        register_failed_attempt(ip)
        assert check_rate_limit(ip) is False

    def test_different_ips_independent(self):
        check_rate_limit("10.0.1.1")
        for _ in range(5):
            register_failed_attempt("10.0.1.1")
        assert check_rate_limit("10.0.1.1") is False
        assert check_rate_limit("10.0.1.2") is True
