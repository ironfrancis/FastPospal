FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 依赖层（利用缓存）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV FASTMCP_STATELESS_HTTP=true

EXPOSE 8000

# 生产 ASGI：uvicorn 多 worker 需 stateless 模式
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
