from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_service
from fastpospal.mcp.fields import (
    Barcode,
    BeginTime,
    EndTime,
    PageIndex,
    PageSize,
    ProductKeyword,
    ProductUid,
)


@mcp.tool
def pospal_list_stock(
    keyword: ProductKeyword = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """分页查全店库存列表（所有商品库存汇总）。

    查单个商品库存优先 pospal_sem_check_product_stock（按名称/条码即可）。
    """
    return get_service().list_stock(
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_stock_change_history(
    barcode: Barcode,
    begin_time: BeginTime,
    end_time: EndTime,
) -> dict[str, Any]:
    """查指定商品条码的库存变更流水。

    时间格式 YYYY-MM-DD HH:mm:ss。需已知条码；不知条码可先 pospal_sem_find_products。
    """
    return get_service().stock_change_history(
        barcode,
        begin_time=begin_time,
        end_time=end_time,
    )


@mcp.tool
def pospal_list_stock_flows(
    begin_time: BeginTime,
    end_time: EndTime,
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """分页查货流单（进货/出库/调拨）列表。

    时间格式 YYYY-MM-DD HH:mm:ss。语义层汇总用 pospal_sem_query_stock_flows。
    """
    return get_service().list_stock_flows(
        begin_time=begin_time,
        end_time=end_time,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_set_product_stock_limit(
    product_uid: ProductUid,
    min_stock: float = 0,
    max_stock: float = 999,
) -> dict[str, Any]:
    """【写】设置商品库存上下限（不直接改库存数量）。

    product_uid 为 UID 字符串（非 productId），来自商品详情或列表。
    """
    return get_service().set_product_stock_limit(
        product_uid,
        min_stock=min_stock,
        max_stock=max_stock,
    )
