import time
from collections import deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class RateLimiter:
    def __init__(self, window: int, max_requests: int):
        self.window = window
        self.max_requests = max_requests
        self.requests = deque()

    def is_allowed(self) -> bool:
        now = time.time()
        window_start = now - self.window

        while self.requests and self.requests[0] < window_start:
            self.requests.popleft()

        if len(self.requests) >= self.max_requests:
            return False

        self.requests.append(now)
        return True


rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    global rate_limiter
    if rate_limiter is None:
        settings = get_settings()
        rate_limiter = RateLimiter(
            window=settings.rate_limit_window,
            max_requests=settings.rate_limit_max_requests,
        )
    return rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path.startswith("/admin") or path == "/health" or path == "/stats":
            return await call_next(request)

        limiter = get_rate_limiter()
        if not limiter.is_allowed():
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        return await call_next(request)
