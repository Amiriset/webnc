from typing import Optional
from webnc.security.auth_provider import AuthProvider

_auth_provider: Optional[AuthProvider] = None


def get_auth_provider():
    return _auth_provider


def set_auth_provider(provider: AuthProvider):
    global _auth_provider
    _auth_provider = provider
