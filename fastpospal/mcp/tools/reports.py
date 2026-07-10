from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_openapi, get_service
from fastpospal.mcp.fields import (
    BeginDatetime,
    BeginTime,
    EndDatetime,
    EndTime,
    OrderSource,
    PageIndex,
    PageSize,
    PaymentMethod,
    TicketSn,
    TicketType,
)


@mcp.tool
def pospal_list_suppliers() -> list[dict[str, Any]]:
    """获取供应商下拉列表（JSON）。用于采购相关场景。"""
    return get_service().list_suppliers()


@mcp.tool
def pospal_business_summary(
    begin_datetime: BeginDatetime,
    end_datetime: EndDatetime,
) -> dict[str, Any]:
    """查门店营业概况（推荐用于日营业额、客单数）。

    返回 metrics：营业实收、充值实收、消耗金额、客单总数等。
    与 pospal_sem_get_store_sales_summary 类似；本工具返回银豹原始指标名。
    时间格式 YYYY-MM-DD HH:mm:ss，查全天示例：00:00:00 ~ 23:59:59。
    """
    return get_service().business_summary(
        begin_datetime=begin_datetime,
        end_datetime=end_datetime,
    )


@mcp.tool
def pospal_recharge_summary(
    begin_datetime: BeginDatetime,
    end_datetime: EndDatetime,
) -> dict[str, Any]:
    """查时段会员充值汇总（总充值金额、总赠送金额、记录数）。

    与营业概况「充值实收」口径一致。不要用 pospal_list_customers 的 summary 查时段充值。
    时间格式 YYYY-MM-DD HH:mm:ss。
    """
    return get_service().recharge_summary(
        begin_datetime=begin_datetime,
        end_datetime=end_datetime,
    )


@mcp.tool
def pospal_list_recharge_logs(
    begin_datetime: BeginDatetime,
    end_datetime: EndDatetime,
    keyword: str = "",
    payment_method: PaymentMethod = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """分页查会员充值明细（会员、金额、赠送、支付方式、时间）。

    汇总金额用 pospal_recharge_summary；本工具返回逐笔明细。时间格式 YYYY-MM-DD HH:mm:ss。
    """
    return get_service().list_recharge_logs(
        begin_datetime=begin_datetime,
        end_datetime=end_datetime,
        keyword=keyword,
        payment_method=payment_method,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_product_sale_summary(
    begin_datetime: BeginDatetime,
    end_datetime: EndDatetime,
    order_source: OrderSource = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """查商品销售明细汇总（总单数、商品实收、利润）及分页明细。

    按分类聚合优先 pospal_sem_query_category_sales。时间 YYYY-MM-DD HH:mm:ss。
    order_source：ZIYING/xianxia/MEITUAN_WAIMAI/ELEME_WAIMAI，留空=全部渠道。
    """
    return get_service().product_sale_summary(
        begin_datetime=begin_datetime,
        end_datetime=end_datetime,
        order_source=order_source,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_list_tickets(
    begin_time: BeginTime,
    end_time: EndTime,
    sn: TicketSn = "",
    ticket_type: TicketType = "0",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """分页查销售单据流水（单号、收银员、金额等）。

    注意：部分门店（如书店）可能始终返回 0 条，不代表无营业。
    查营业额用 pospal_business_summary；逐笔流水用 pospal_sem_query_sales_detail。
    时间 YYYY-MM-DD HH:mm:ss。ticket_type：0=有效, 1=作废, 4=退货, 2=会员, 3=批发。
    """
    return get_service().list_tickets(
        begin_time=begin_time,
        end_time=end_time,
        sn=sn,
        ticket_type=ticket_type,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_list_eshop_orders(
    begin_time: BeginTime,
    end_time: EndTime,
    keyword: str = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """分页查自营网单。

    时间格式 YYYY-MM-DD HH:mm:ss。keyword 可筛单号/收货人/手机等。
    """
    return get_service().list_eshop_orders(
        begin_time=begin_time,
        end_time=end_time,
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_list_product_purchases(
    begin_time: BeginTime,
    end_time: EndTime,
    keyword: str = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
) -> dict[str, Any]:
    """分页查采购单。

    时间格式 YYYY-MM-DD HH:mm:ss。keyword 可筛单号/供应商/商品等。
    """
    return get_service().list_product_purchases(
        begin_time=begin_time,
        end_time=end_time,
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
    )


@mcp.tool
def pospal_openapi_status() -> dict[str, Any]:
    """检查银豹官方开放平台 appId/appKey 是否已配置。

    返回 configured 与 hint；未配置不影响 Web API 工具使用。
    """
    client = get_openapi()
    return {
        "configured": client is not None,
        "hint": "向银豹业务申请 appId/appKey 后设置 POSPAL_APP_ID / POSPAL_APP_KEY",
    }
