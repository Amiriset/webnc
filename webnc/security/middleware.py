from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from webnc.security._state import get_auth_provider


class SessionAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path in ("/api/health", "/api/drives", "/api/disk"):
            return await call_next(request)
        provider = get_auth_provider()
        if not provider:
            return JSONResponse(
                status_code=401,
                content={"detail": "No auth provider configured"},
            )
        user = await provider.authenticate(request)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"},
            )
        request.state.user_info = user
        return await call_next(request)
