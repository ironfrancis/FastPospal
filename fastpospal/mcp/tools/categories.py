from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_service
from fastpospal.mcp.fields import CategoryUid


@mcp.tool
def pospal_list_categories() -> list[dict[str, Any]]:
    """获取商品分类树（JSON 嵌套结构）。

    返回含 name、uid、children 等字段。创建/更新商品需 category_uid 时可先调用本工具。
    自然语言查分类销售请用 pospal_sem_query_category_sales，无需先拉全部分类。
    """
    return get_service().list_categories()


@mcp.tool
def pospal_create_category(name: str, parent_name: str = "") -> dict[str, Any]:
    """【写】创建商品分类。

    name 为新分类名；parent_name 为空则创建顶级分类，否则挂到同名父分类下。
    """
    return get_service().create_category(name, parent_name=parent_name)


@mcp.tool
def pospal_update_category(
    category_uid: CategoryUid,
    new_name: str,
    parent_name: str = "",
) -> dict[str, Any]:
    """【写】重命名分类。

    category_uid 来自 list_categories；parent_name 可选，用于调整父级。
    """
    return get_service().update_category(category_uid, new_name, parent_name=parent_name)


@mcp.tool
def pospal_delete_categories(category_uids: list[str]) -> dict[str, Any]:
    """【写】批量删除分类。

    category_uids 为 uid 字符串列表（来自 list_categories）。删除后不可恢复。
    """
    return get_service().delete_categories(category_uids)
