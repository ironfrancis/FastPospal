"""FastPospal MCP Server 入口。"""

from __future__ import annotations

import os

from fastpospal.mcp import mcp  # noqa: F401 — 导入时注册全部工具

__all__ = ["mcp", "main"]


def main() -> None:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
