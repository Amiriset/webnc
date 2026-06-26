"""Tests for webnc.security.console_token — ConsoleTokenProvider."""
import hashlib
import time

import pytest

from webnc.security.console_token import ConsoleTokenProvider
from webnc.models.auth import UserInfo


@pytest.fixture
def provider():
    return ConsoleTokenProvider()


def _make_headers(provider, nonce, ts):
    sig = hashlib.sha256(f"{nonce}{ts}{provider.token}".encode()).hexdigest()
    return {
        "X-NC-Nonce": nonce,
        "X-NC-Timestamp": str(ts),
        "X-NC-Signature": sig,
    }


class _FakeRequest:
    def __init__(self, headers):
        self.headers = headers


class TestTokenGeneration:
    def test_token_is_64_hex_chars(self, provider):
        assert len(provider.token) == 64
        int(provider.token, 16)  # should not raise

    def test_tokens_are_unique(self):
        p1 = ConsoleTokenProvider()
        p2 = ConsoleTokenProvider()
        assert p1.token != p2.token


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_valid_auth(self, provider):
        nonce = "test-nonce-1"
        ts = str(time.time())
        req = _FakeRequest(_make_headers(provider, nonce, ts))
        result = await provider.authenticate(req)
        assert result is not None
        assert isinstance(result, UserInfo)
        assert result.username == "admin"
        assert "admin" in result.roles

    @pytest.mark.asyncio
    async def test_missing_headers_returns_none(self, provider):
        req = _FakeRequest({})
        result = await provider.authenticate(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_nonce(self, provider):
        ts = str(time.time())
        sig = hashlib.sha256(f"nonce{ts}{provider.token}".encode()).hexdigest()
        req = _FakeRequest({
            "X-NC-Timestamp": ts,
            "X-NC-Signature": sig,
        })
        result = await provider.authenticate(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_wrong_signature(self, provider):
        nonce = "test-nonce"
        ts = str(time.time())
        req = _FakeRequest({
            "X-NC-Nonce": nonce,
            "X-NC-Timestamp": ts,
            "X-NC-Signature": "wrong_signature",
        })
        result = await provider.authenticate(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_timestamp(self, provider):
        nonce = "test-nonce"
        ts = str(time.time() - 600)  # 10 minutes ago
        req = _FakeRequest(_make_headers(provider, nonce, ts))
        result = await provider.authenticate(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_timestamp_format(self, provider):
        nonce = "test-nonce"
        req = _FakeRequest({
            "X-NC-Nonce": nonce,
            "X-NC-Timestamp": "not-a-number",
            "X-NC-Signature": "whatever",
        })
        result = await provider.authenticate(req)
        assert result is None

    @pytest.mark.asyncio
    async def test_nonce_replay_rejected(self, provider):
        nonce = "replay-nonce"
        ts = str(time.time())
        headers = _make_headers(provider, nonce, ts)
        req1 = _FakeRequest(headers)
        result1 = await provider.authenticate(req1)
        assert result1 is not None

        req2 = _FakeRequest(headers)
        result2 = await provider.authenticate(req2)
        assert result2 is None

    @pytest.mark.asyncio
    async def test_different_nonces_accepted(self, provider):
        ts = str(time.time())
        req1 = _FakeRequest(_make_headers(provider, "nonce1", ts))
        req2 = _FakeRequest(_make_headers(provider, "nonce2", ts))
        assert await provider.authenticate(req1) is not None
        assert await provider.authenticate(req2) is not None


class TestNonceCleanup:
    @pytest.mark.asyncio
    async def test_nonce_set_cleared_at_10000(self, provider):
        ts = str(time.time())
        for i in range(10001):
            nonce = f"nonce-{i}"
            headers = _make_headers(provider, nonce, ts)
            req = _FakeRequest(headers)
            await provider.authenticate(req)

        assert len(provider._used_nonces) == 0
