from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_service


@mcp.tool
def pospal_session_info() -> dict[str, Any]:
    """查看当前银豹登录会话。

    返回账号、门店名称、子域、userId、logged_in 等。排查鉴权或确认当前门店时优先调用。
    """
    return get_service().client.session_info()


@mcp.tool
def pospal_login() -> dict[str, Any]:
    """强制重新登录银豹云后台，刷新会话 cookie。

    仅在 session 失效或切换账号后使用；正常调用其它工具会自动维持登录。
    """
    get_service.cache_clear()
    return get_service().client.login(force=True)
