"""ASGI 入口，供 uvicorn / gunicorn 生产部署。"""

from __future__ import annotations

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from server import mcp

app = mcp.http_app()


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """可选 Bearer Token 鉴权。设置环境变量 MCP_AUTH_TOKEN 后生效。"""

    async def dispatch(self, request: Request, call_next):
        expected = os.environ.get("MCP_AUTH_TOKEN", "").strip()
        if not expected:
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {expected}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


app.add_middleware(BearerAuthMiddleware)
