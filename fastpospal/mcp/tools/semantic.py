from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_semantic
from fastpospal.mcp.fields import (
    CategoryName,
    EndDate,
    SemCompact,
    SemKeyword,
    SemLimit,
    SemPage,
    SemSearch,
    SemSize,
    ShopNames,
    StartDate,
)


@mcp.tool
def pospal_sem_find_products(
    keyword: SemKeyword,
    limit: SemLimit = 5,
    shop_names: ShopNames = "",
) -> dict[str, Any]:
    """按名称或条码搜索商品档案（推荐）。

    返回名称、价格、分类、条码等。精确条码且需完整 JSON 时用 pospal_find_product_by_barcode。
    返回 {ok: true, data: {products, total}}。
    """
    return get_semantic().find_products(keyword, limit=limit, shop_names=shop_names or None)


@mcp.tool
def pospal_sem_check_product_stock(
    keyword: SemKeyword,
    shop_names: ShopNames = "",
) -> dict[str, Any]:
    """查询单个商品当前实时库存（推荐）。

    按名称或条码匹配第一件商品。查全店库存列表用 pospal_list_stock。
    """
    return get_semantic().check_product_stock(keyword, shop_names=shop_names or None)


@mcp.tool
def pospal_sem_query_category_sales(
    category_name: CategoryName,
    start_date: StartDate = "",
    end_date: EndDate = "",
    shop_names: ShopNames = "",
    limit: SemLimit = 30,
) -> dict[str, Any]:
    """查询某分类商品的销售聚合（推荐）。

    自动识别分类，无需先 list_categories。日期 YYYY-MM-DD，留空默认近 7 天。
    原始层报表字段用 pospal_product_sale_summary。
    """
    return get_semantic().query_category_sales(
        category_name,
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
        limit=limit,
    )


@mcp.tool
def pospal_sem_get_store_sales_summary(
    start_date: StartDate = "",
    end_date: EndDate = "",
    shop_names: ShopNames = "",
) -> dict[str, Any]:
    """获取全店销售汇总：总营业额、总交易笔数等（推荐）。

    日期 YYYY-MM-DD，留空默认近 7 天。银豹原始指标名用 pospal_business_summary。
    """
    return get_semantic().get_store_sales_summary(
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
    )


@mcp.tool
def pospal_sem_query_sales_detail(
    search: SemSearch = "",
    start_date: StartDate = "",
    end_date: EndDate = "",
    shop_names: ShopNames = "",
    page: SemPage = 1,
    size: SemSize = 20,
    compact: SemCompact = False,
) -> dict[str, Any]:
    """查询逐笔销售明细流水（推荐）。

    search 可按商品名/条码/分类筛选；日期 YYYY-MM-DD。compact=true 压缩列。
    部分门店 pospal_list_tickets 恒为 0，请用本工具。
    """
    return get_semantic().query_sales_detail(
        search=search or None,
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
        page=page,
        size=size,
        compact=compact,
    )


@mcp.tool
def pospal_sem_query_stock_flows(
    start_date: StartDate = "",
    end_date: EndDate = "",
    shop_names: ShopNames = "",
    page: SemPage = 1,
    size: SemSize = 20,
    compact: SemCompact = False,
) -> dict[str, Any]:
    """查询库存流水（入库、出库、盘点等）。

    日期 YYYY-MM-DD。原始货流单列表用 pospal_list_stock_flows。
    """
    return get_semantic().query_stock_flows(
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
        page=page,
        size=size,
        compact=compact,
    )


@mcp.tool
def pospal_sem_list_products_admin(
    page: SemPage = 1,
    size: SemSize = 20,
    keyword: SemKeyword = "",
    shop_names: ShopNames = "",
    compact: SemCompact = False,
) -> dict[str, Any]:
    """管理员分页浏览完整商品列表。

    大范围浏览用本工具；按关键词找少量商品用 pospal_sem_find_products。
    """
    return get_semantic().list_products_admin(
        page=page,
        size=size,
        keyword=keyword,
        shop_names=shop_names or None,
        compact=compact,
    )


@mcp.tool
def pospal_sem_analyze_restock_needs(
    days: int = 3,
    shop_names: ShopNames = "",
    hot_threshold: float = 0.5,
    urgent_threshold: float = 0.8,
    sold_out_threshold: float = 1.0,
) -> dict[str, Any]:
    """分析需补货商品（综合近 N 天销量与当前库存）。

    days 默认 3；threshold 控制热销/紧急/售罄判定（0~1）。
    """
    return get_semantic().analyze_restock_needs(
        days=days,
        shop_names=shop_names or None,
        hot_threshold=hot_threshold,
        urgent_threshold=urgent_threshold,
        sold_out_threshold=sold_out_threshold,
    )
