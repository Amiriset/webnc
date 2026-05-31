import hashlib
import secrets
import time
from typing import Optional

from webnc.logging_config import logger
from webnc.models.auth import UserInfo
from webnc.security.auth_provider import AuthProvider


class ConsoleTokenProvider(AuthProvider):
    """Zero-knowledge token auth: SHA-256(nonce + ts + secret) handshake."""

    def __init__(self):
        self.token = secrets.token_hex(32)
        self._used_nonces: set = set()
        logger.info("=" * 60)
        logger.info("SECURITY: Admin access token for this session:")
        logger.info(self.token)
        logger.info(
            "Paste this token when prompted in the browser, "
            "or append #token=<TOKEN> to the URL."
        )
        logger.info("=" * 60)

    async def authenticate(self, request) -> Optional[UserInfo]:
        nonce = request.headers.get("X-NC-Nonce")
        sig = request.headers.get("X-NC-Signature")
        ts = request.headers.get("X-NC-Timestamp")
        if not nonce or not sig or not ts:
            return None
        try:
            if abs(time.time() - float(ts)) > 300:
                return None
        except ValueError:
            return None
        if nonce in self._used_nonces:
            return None
        expected = hashlib.sha256(
            f"{nonce}{ts}{self.token}".encode()
        ).hexdigest()
        if not secrets.compare_digest(sig, expected):
            return None
        self._used_nonces.add(nonce)
        if len(self._used_nonces) > 10000:
            self._used_nonces.clear()
        return UserInfo(username="admin", roles=["admin"])
