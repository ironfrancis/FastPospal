from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_service
from fastpospal.mcp.fields import (
    Barcode,
    CategoryUid,
    PageIndex,
    PageSize,
    ProductEnable,
    ProductId,
    ProductKeyword,
)


@mcp.tool
def pospal_product_summary(
    keyword: ProductKeyword = "",
    enable: ProductEnable = "1",
) -> dict[str, Any]:
    """统计商品数量（totalRecord）。

    keyword 支持条码/名称/拼音码筛选；enable：1=启用, 0=禁用。
    仅需数量时用本工具；需列表详情用 pospal_list_products 或 pospal_sem_find_products。
    """
    result = get_service().product_summary(keyword=keyword, enable=enable)
    return {
        "successed": result.get("successed"),
        "totalRecord": result.get("totalRecord", 0),
        "keyword": keyword,
    }


@mcp.tool
def pospal_list_products(
    keyword: ProductKeyword = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
    enable: ProductEnable = "1",
) -> dict[str, Any]:
    """分页查询商品列表（原始层，含完整字段）。

    返回 products 数组与 totalRecord。按名称/条码模糊查找优先 pospal_sem_find_products；
    已知 productId 查详情用 pospal_get_product。
    """
    return get_service().list_products(
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
        enable=enable,
    )


@mcp.tool
def pospal_get_product(product_id: ProductId) -> dict[str, Any]:
    """按 productId 获取商品详情 JSON。

    productId 为数字 ID（非 productUid）。更新商品前可先调用以获取完整 payload。
    """
    return get_service().get_product(product_id)


@mcp.tool
def pospal_find_product_by_barcode(barcode: Barcode) -> dict[str, Any]:
    """按条码精确查商品详情（原始层）。

    需完整条码。按名称模糊搜索请用 pospal_sem_find_products。
    """
    return get_service().find_product_by_barcode(barcode)


@mcp.tool
def pospal_create_product(
    name: str,
    barcode: Barcode = "",
    category_uid: CategoryUid = "",
    sell_price: str = "9.99",
    buy_price: str = "5.00",
) -> dict[str, Any]:
    """【写】创建测试商品。

    barcode 为空则自动生成；category_uid 为空则用第一个分类。仅测试账号使用。
    """
    return get_service().create_product(
        name,
        barcode or None,
        category_uid=category_uid or None,
        sell_price=sell_price,
        buy_price=buy_price,
    )


@mcp.tool
def pospal_update_product(
    product_id: ProductId,
    name: str = "",
    sell_price: str = "",
    buy_price: str = "",
    enable: str = "",
) -> dict[str, Any]:
    """【写】更新商品字段（仅传需要修改的字段）。

    enable：1=启用, 0=禁用。至少提供一个非空字段，否则报错。
    """
    changes: dict[str, Any] = {}
    if name:
        changes["name"] = name
    if sell_price:
        changes["sellPrice"] = sell_price
    if buy_price:
        changes["buyPrice"] = buy_price
    if enable:
        changes["enable"] = enable
    if not changes:
        raise ValueError("至少提供一个要修改的字段")
    return get_service().update_product(product_id, **changes)


@mcp.tool
def pospal_delete_product(product_id: ProductId) -> dict[str, Any]:
    """【写】删除商品（不可恢复，仅测试账号使用）。"""
    return get_service().delete_product(product_id)
