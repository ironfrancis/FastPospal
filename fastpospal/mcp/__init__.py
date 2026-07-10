"""FastPospal MCP Server 核心。"""

from __future__ import annotations

from fastpospal.mcp.instance import MCP_INSTRUCTIONS, mcp

# 导入工具模块以触发 @mcp.tool 注册
import fastpospal.mcp.tools  # noqa: F401

__all__ = ["mcp", "MCP_INSTRUCTIONS"]
