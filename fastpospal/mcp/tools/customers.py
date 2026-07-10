from __future__ import annotations

from typing import Any

from fastpospal.mcp.instance import mcp
from fastpospal.mcp.deps import get_service
from fastpospal.mcp.fields import CustomerNumber, CustomerType, PageIndex, PageSize


@mcp.tool
def pospal_find_customer(number: CustomerNumber) -> dict[str, Any]:
    """按会员卡号或手机号查单个会员详情。

    返回 {found, customer} 或 {found: false}。查列表用 pospal_list_customers。
    """
    customer = get_service().find_customer(number)
    if not customer:
        return {"found": False, "number": number}
    return {"found": True, "customer": customer}


@mcp.tool
def pospal_list_customers(
    keyword: str = "",
    page_index: PageIndex = 1,
    page_size: PageSize = 20,
    customer_type: CustomerType = "1",
) -> dict[str, Any]:
    """分页查会员列表。

    keyword 可搜卡号/姓名/手机；customer_type：1=启用, 0=禁用, 2=过期。
    注意：summary 为全店会员统计，不能用于查时段充值；时段充值用 pospal_recharge_summary。
    """
    return get_service().list_customers(
        keyword=keyword,
        page_index=page_index,
        page_size=page_size,
        customer_type=customer_type,
    )


@mcp.tool
def pospal_get_customer_extras(number: CustomerNumber) -> dict[str, Any]:
    """查会员附属信息：次卡、权益卡、购物卡、优惠券。"""
    return get_service().get_customer_extras(number)


@mcp.tool
def pospal_create_customer(
    number: CustomerNumber,
    name: str,
    tel: str = "",
    remarks: str = "",
) -> dict[str, Any]:
    """【写】创建会员。number 为会员卡号（删除后不可复用）。"""
    return get_service().create_customer(number, name, tel=tel, remarks=remarks)


@mcp.tool
def pospal_update_customer(
    number: CustomerNumber,
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
    return get_service().update_customer(number, **changes)


@mcp.tool
def pospal_delete_customer(number: CustomerNumber) -> dict[str, Any]:
    """【写】软删除会员（enable=-1，卡号不可复用）。"""
    return get_service().delete_customer(number)
