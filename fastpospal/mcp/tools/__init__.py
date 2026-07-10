"""导入各业务域工具模块，触发 @mcp.tool 注册。"""

from fastpospal.mcp.tools import (  # noqa: F401
    categories,
    customers,
    products,
    reports,
    semantic,
    session,
    stock,
)
