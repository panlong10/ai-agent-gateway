from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


async def verify_api_key(request: Request) -> str | None:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    return api_key


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path.startswith("/admin") or path == "/health" or path == "/stats":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing X-API-Key header"},
            )

        settings = get_settings()
        if api_key == settings.admin_api_key:
            request.state.is_admin = True
            return await call_next(request)

        request.state.is_admin = False
        request.state.agent_api_key = api_key

        return await call_next(request)
