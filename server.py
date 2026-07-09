from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from fastpospal.client import PospalClient
from fastpospal.openapi import PospalOpenApiClient
from fastpospal.service import PospalService
from fastpospal.semantic.service import PospalSemanticService

load_dotenv()

mcp = FastMCP(
    "FastPospal",
    instructions=(
        "银豹 PosPal 门店 MCP 服务。封装银豹云后台 Web API，"
        "支持商品/分类/会员/库存/货流/单据/网单/采购的读写操作。"
        "写操作会修改门店真实数据，仅在测试账号或明确授权时使用。"
        "环境变量：POSPAL_ACCOUNT, POSPAL_PASSWORD。"
        "查日营业额/客单数优先用 pospal_business_summary 或 pospal_sem_get_store_sales_summary；"
        "查商品级销售汇总用 pospal_product_sale_summary 或 pospal_sem_query_category_sales；"
        "按名称/条码找商品优先 pospal_sem_find_products；"
        "pospal_list_tickets 在部分门店可能始终返回 0，不能据此判断无营业。"
    ),
)


@lru_cache(maxsize=1)
def _get_service() -> PospalService:
    account = os.environ.get("POSPAL_ACCOUNT", "")
    password = os.environ.get("POSPAL_PASSWORD", "")
    if not account or not password:
        raise RuntimeError("请设置环境变量 POSPAL_ACCOUNT 和 POSPAL_PASSWORD")
    client = PospalClient(account=account, password=password)
    client.login()
    return PospalService(client)


@lru_cache(maxsize=1)
def _get_semantic() -> PospalSemanticService:
    return PospalSemanticService(_get_service())


@lru_cache(maxsize=1)
def _get_openapi() -> PospalOpenApiClient | None:
    app_id = os.environ.get("POSPAL_APP_ID")
    app_key = os.environ.get("POSPAL_APP_KEY")
    if not app_id or not app_key:
        return None
    host = os.environ.get("POSPAL_OPENAPI_HOST", "https://area-openapi.pospal.cn")
    return PospalOpenApiClient(app_id, app_key, host=host)


# ── 会话 ────────────────────────────────────────────────


@mcp.tool
def pospal_session_info() -> dict[str, Any]:
    """查看当前银豹登录会话（账号、门店名称、子域、userId、是否有效）。"""
    return _get_service().client.session_info()


@mcp.tool
def pospal_login() -> dict[str, Any]:
    """强制重新登录银豹云后台，刷新会话 cookie。"""
    _get_service.cache_clear()
    return _get_service().client.login(force=True)


# ── 分类（读 + 写） ─────────────────────────────────────


@mcp.tool
def pospal_list_categories() -> list[dict[str, Any]]:
    """获取商品分类树（JSON）。"""
    return _get_service().list_categories()


@mcp.tool
def pospal_create_category(name: str, parent_name: str = "") -> dict[str, Any]:
    """【写】创建商品分类。parent_name 为空则创建顶级分类。"""
    return _get_service().create_category(name, parent_name=parent_name)


@mcp.tool
def pospal_update_category(category_uid: str, new_name: str, parent_name: str = "") -> dict[str, Any]:
    """【写】重命名分类。"""
    return _get_service().update_category(category_uid, new_name, parent_name=parent_name)


@mcp.tool
def pospal_delete_categories(category_uids: list[str]) -> dict[str, Any]:
    """【写】批量删除分类（category_uids 为 uid 字符串列表）。"""
    return _get_service().delete_categories(category_uids)


# ── 商品（读） ──────────────────────────────────────────


@mcp.tool
def pospal_product_summary(keyword: str = "", enable: str = "1") -> dict[str, Any]:
    """商品数量统计。keyword 支持条码/名称/拼音码。"""
    result = _get_service().product_summary(keyword=keyword, enable=enable)
    return {
        "successed": result.get("successed"),
        "totalRecord": result.get("totalRecord", 0),
        "keyword": keyword,
    }


@mcp.tool
def pospal_list_products(
    keyword: str = "",
    page_index: int = 1,
    page_size: int = 20,
    enable: str = "1",
) -> dict[str, Any]:
    """分页查询商品列表（HTML 解析为结构化数据）。"""
    return _get_service().list_products(
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
        enable=enable,
    )


@mcp.tool
def pospal_get_product(product_id: int) -> dict[str, Any]:
    """按 productId 获取商品详情 JSON。"""
    return _get_service().get_product(product_id)


@mcp.tool
def pospal_find_product_by_barcode(barcode: str) -> dict[str, Any]:
    """按条码查商品详情。"""
    return _get_service().find_product_by_barcode(barcode)


# ── 商品（写） ──────────────────────────────────────────


@mcp.tool
def pospal_create_product(
    name: str,
    barcode: str = "",
    category_uid: str = "",
    sell_price: str = "9.99",
    buy_price: str = "5.00",
) -> dict[str, Any]:
    """【写】创建测试商品。barcode 为空则自动生成；category_uid 为空则用第一个分类。"""
    return _get_service().create_product(
        name,
        barcode or None,
        category_uid=category_uid or None,
        sell_price=sell_price,
        buy_price=buy_price,
    )


@mcp.tool
def pospal_update_product(
    product_id: int,
    name: str = "",
    sell_price: str = "",
    buy_price: str = "",
    enable: str = "",
) -> dict[str, Any]:
    """【写】更新商品字段（仅传需要修改的字段）。"""
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
    return _get_service().update_product(product_id, **changes)


@mcp.tool
def pospal_delete_product(product_id: int) -> dict[str, Any]:
    """【写】删除商品（不可恢复，仅测试账号使用）。"""
    return _get_service().delete_product(product_id)


# ── 会员（读） ──────────────────────────────────────────


@mcp.tool
def pospal_find_customer(number: str) -> dict[str, Any]:
    """按会员卡号/手机号查会员详情 JSON。"""
    customer = _get_service().find_customer(number)
    if not customer:
        return {"found": False, "number": number}
    return {"found": True, "customer": customer}


@mcp.tool
def pospal_list_customers(
    keyword: str = "",
    page_index: int = 1,
    page_size: int = 20,
    customer_type: str = "1",
) -> dict[str, Any]:
    """分页查会员列表。customer_type: 1=启用, 0=禁用, 2=过期。"""
    return _get_service().list_customers(
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
        customer_type=customer_type,
    )


@mcp.tool
def pospal_get_customer_extras(number: str) -> dict[str, Any]:
    """查会员附属信息：次卡、权益卡、购物卡、优惠券。"""
    return _get_service().get_customer_extras(number)


# ── 会员（写） ──────────────────────────────────────────


@mcp.tool
def pospal_create_customer(
    number: str,
    name: str,
    tel: str = "",
    remarks: str = "",
) -> dict[str, Any]:
    """【写】创建会员。number 为会员卡号（删除后不可复用）。"""
    return _get_service().create_customer(number, name, tel=tel, remarks=remarks)


@mcp.tool
def pospal_update_customer(
    number: str,
    name: str = "",
    tel: str = "",
    remarks: str = "",
) -> dict[str, Any]:
    """【写】更新会员资料。余额/积分修改需门店开启 editMoneyPoint 权限。"""
    changes: dict[str, Any] = {}
    if name:
        changes["name"] = name
    if tel:
        changes["tel"] = tel
    if remarks:
        changes["remarks"] = remarks
    if not changes:
        raise ValueError("至少提供一个要修改的字段")
    return _get_service().update_customer(number, **changes)


@mcp.tool
def pospal_delete_customer(number: str) -> dict[str, Any]:
    """【写】软删除会员（enable=-1，卡号不可复用）。"""
    return _get_service().delete_customer(number)


# ── 库存 / 货流 ─────────────────────────────────────────


@mcp.tool
def pospal_list_stock(
    keyword: str = "",
    page_index: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """分页查库存列表（全店商品库存汇总）。"""
    return _get_service().list_stock(keyword=keyword, page_index=page_index, page_size=page_size)


@mcp.tool
def pospal_stock_change_history(
    barcode: str,
    begin_time: str,
    end_time: str,
) -> dict[str, Any]:
    """查指定商品条码的库存变更流水。"""
    return _get_service().stock_change_history(barcode, begin_time=begin_time, end_time=end_time)


@mcp.tool
def pospal_list_stock_flows(
    begin_time: str,
    end_time: str,
    page_index: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """分页查货流单（进货/出库/调拨）列表。"""
    return _get_service().list_stock_flows(
        begin_time=begin_time,
        end_time=end_time,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_set_product_stock_limit(
    product_uid: str,
    min_stock: float = 0,
    max_stock: float = 999,
) -> dict[str, Any]:
    """【写】设置商品库存上下限（不直接改库存数量）。"""
    return _get_service().set_product_stock_limit(
        product_uid, min_stock=min_stock, max_stock=max_stock
    )


# ── 供应商 / 单据 / 网单 / 采购 ─────────────────────────


@mcp.tool
def pospal_list_suppliers() -> list[dict[str, Any]]:
    """获取供应商下拉列表（JSON）。"""
    return _get_service().list_suppliers()


@mcp.tool
def pospal_business_summary(
    begin_datetime: str,
    end_datetime: str,
) -> dict[str, Any]:
    """查门店营业概况（推荐用于日营业额、客单数）。

    返回营业实收、消耗金额、客单总数等指标。时间格式：YYYY-MM-DD HH:mm:ss，
    例如查 2026-07-08 全天：begin_datetime=2026-07-08 00:00:00，end_datetime=2026-07-08 23:59:59。
    """
    return _get_service().business_summary(
        begin_datetime=begin_datetime,
        end_datetime=end_datetime,
    )


@mcp.tool
def pospal_product_sale_summary(
    begin_datetime: str,
    end_datetime: str,
    order_source: str = "",
    page_index: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """查商品销售明细汇总（总单数、商品实收、利润）及分页明细。

    时间格式：YYYY-MM-DD HH:mm:ss。order_source 可选：ZIYING=自营、xianxia=线下订单，
    MEITUAN_WAIMAI=美团、ELEME_WAIMAI=饿了么；留空表示全部渠道。
    """
    return _get_service().product_sale_summary(
        begin_datetime=begin_datetime,
        end_datetime=end_datetime,
        order_source=order_source,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_list_tickets(
    begin_time: str,
    end_time: str,
    sn: str = "",
    ticket_type: str = "0",
    page_index: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """分页查销售单据流水（单号、收银员、金额等明细）。

    注意：部分门店（如书店）该接口可能始终返回 0 条，不代表无营业。
    查日营业额请用 pospal_business_summary；查商品销售汇总请用 pospal_product_sale_summary。

    时间格式：YYYY-MM-DD HH:mm:ss。ticket_type: 0=有效, 1=作废, 4=退货, 2=会员, 3=批发。
    """
    return _get_service().list_tickets(
        begin_time=begin_time,
        end_time=end_time,
        sn=sn,
        ticket_type=ticket_type,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_list_eshop_orders(
    begin_time: str,
    end_time: str,
    keyword: str = "",
    page_index: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """分页查自营网单。"""
    return _get_service().list_eshop_orders(
        begin_time=begin_time,
        end_time=end_time,
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_list_product_purchases(
    begin_time: str,
    end_time: str,
    keyword: str = "",
    page_index: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """分页查采购单。"""
    return _get_service().list_product_purchases(
        begin_time=begin_time,
        end_time=end_time,
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_openapi_status() -> dict[str, Any]:
    """检查银豹官方开放平台 appId/appKey 是否已配置。"""
    client = _get_openapi()
    return {
        "configured": client is not None,
        "hint": "向银豹业务申请 appId/appKey 后设置 POSPAL_APP_ID / POSPAL_APP_KEY",
    }


# ── 语义层（pospal_sem_*） ───────────────────────────────


@mcp.tool
def pospal_sem_find_products(keyword: str, limit: int = 5, shop_names: str = "") -> dict[str, Any]:
    """按名称或条码搜索商品档案（名称、价格、分类、条码）。"""
    return _get_semantic().find_products(keyword, limit=limit, shop_names=shop_names or None)


@mcp.tool
def pospal_sem_check_product_stock(keyword: str, shop_names: str = "") -> dict[str, Any]:
    """查询商品当前实时库存数量。"""
    return _get_semantic().check_product_stock(keyword, shop_names=shop_names or None)


@mcp.tool
def pospal_sem_query_category_sales(
    category_name: str,
    start_date: str = "",
    end_date: str = "",
    shop_names: str = "",
    limit: int = 30,
) -> dict[str, Any]:
    """查询某类商品的销售聚合（自动识别分类，无需先查分类列表）。"""
    return _get_semantic().query_category_sales(
        category_name,
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
        limit=limit,
    )


@mcp.tool
def pospal_sem_get_store_sales_summary(
    start_date: str = "",
    end_date: str = "",
    shop_names: str = "",
) -> dict[str, Any]:
    """获取全店整体销售汇总（总营业额、总交易笔数等）。"""
    return _get_semantic().get_store_sales_summary(
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
    )


@mcp.tool
def pospal_sem_query_sales_detail(
    search: str = "",
    start_date: str = "",
    end_date: str = "",
    shop_names: str = "",
    page: int = 1,
    size: int = 20,
    compact: bool = False,
) -> dict[str, Any]:
    """查询逐笔销售明细流水（可按商品名/条码/分类关键词筛选）。"""
    return _get_semantic().query_sales_detail(
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
    start_date: str = "",
    end_date: str = "",
    shop_names: str = "",
    page: int = 1,
    size: int = 20,
    compact: bool = False,
) -> dict[str, Any]:
    """查询库存流水记录（入库、出库、盘点等变动）。"""
    return _get_semantic().query_stock_flows(
        start_date=start_date or None,
        end_date=end_date or None,
        shop_names=shop_names or None,
        page=page,
        size=size,
        compact=compact,
    )


@mcp.tool
def pospal_sem_list_products_admin(
    page: int = 1,
    size: int = 20,
    keyword: str = "",
    shop_names: str = "",
    compact: bool = False,
) -> dict[str, Any]:
    """管理员分页浏览完整商品列表。"""
    return _get_semantic().list_products_admin(
        page=page,
        size=size,
        keyword=keyword,
        shop_names=shop_names or None,
        compact=compact,
    )


@mcp.tool
def pospal_sem_analyze_restock_needs(
    days: int = 3,
    shop_names: str = "",
    hot_threshold: float = 0.5,
    urgent_threshold: float = 0.8,
    sold_out_threshold: float = 1.0,
) -> dict[str, Any]:
    """分析哪些商品需要补货（综合库存与近期销量）。"""
    return _get_semantic().analyze_restock_needs(
        days=days,
        shop_names=shop_names or None,
        hot_threshold=hot_threshold,
        urgent_threshold=urgent_threshold,
        sold_out_threshold=sold_out_threshold,
    )


def main() -> None:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
