import time
import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        settings = get_settings()

        request_body = None
        if settings.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    request_body = body.decode("utf-8")
                except:
                    request_body = "<binary data>"
            request._body = body

        client_ip = request.client.host if request.client else None

        response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)

        response_body = None
        if settings.log_response_body:
            response_body = (
                response.body.decode("utf-8") if hasattr(response, "body") else None
            )

        log_data = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "ip_address": client_ip,
            "request_body": request_body,
            "response_body": response_body,
        }

        request.state.log_data = log_data

        return response
