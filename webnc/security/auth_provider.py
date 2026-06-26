from abc import ABC, abstractmethod
from typing import Optional

from webnc.models.auth import UserInfo


class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, request) -> Optional[UserInfo]:
        ...

    async def authorize(self, user: UserInfo, permission: str) -> bool:
        return "admin" in user.roles
