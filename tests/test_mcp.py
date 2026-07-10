"""MCP Server 注册与工具说明测试（离线，不依赖银豹账号）。"""

from __future__ import annotations

import asyncio

import pytest

from fastpospal.mcp import mcp
from fastpospal.mcp.instance import MCP_INSTRUCTIONS

EXPECTED_TOOLS = {
    "pospal_session_info",
    "pospal_login",
    "pospal_list_categories",
    "pospal_create_category",
    "pospal_update_category",
    "pospal_delete_categories",
    "pospal_product_summary",
    "pospal_list_products",
    "pospal_get_product",
    "pospal_find_product_by_barcode",
    "pospal_create_product",
    "pospal_update_product",
    "pospal_delete_product",
    "pospal_find_customer",
    "pospal_list_customers",
    "pospal_get_customer_extras",
    "pospal_create_customer",
    "pospal_update_customer",
    "pospal_delete_customer",
    "pospal_list_stock",
    "pospal_stock_change_history",
    "pospal_list_stock_flows",
    "pospal_set_product_stock_limit",
    "pospal_list_suppliers",
    "pospal_business_summary",
    "pospal_recharge_summary",
    "pospal_list_recharge_logs",
    "pospal_product_sale_summary",
    "pospal_list_tickets",
    "pospal_list_eshop_orders",
    "pospal_list_product_purchases",
    "pospal_openapi_status",
    "pospal_sem_find_products",
    "pospal_sem_check_product_stock",
    "pospal_sem_query_category_sales",
    "pospal_sem_get_store_sales_summary",
    "pospal_sem_query_sales_detail",
    "pospal_sem_query_stock_flows",
    "pospal_sem_list_products_admin",
    "pospal_sem_analyze_restock_needs",
}


def _tool_map() -> dict[str, object]:
    tools = asyncio.run(mcp.list_tools())
    return {t.name: t for t in tools}


def test_all_tools_registered():
    names = set(_tool_map())
    assert names == EXPECTED_TOOLS


def test_instructions_include_routing_guide():
    assert "pospal_business_summary" in MCP_INSTRUCTIONS
    assert "pospal_sem_find_products" in MCP_INSTRUCTIONS
    assert "YYYY-MM-DD" in MCP_INSTRUCTIONS


def test_key_tools_have_descriptions():
    tools = _tool_map()
    biz = tools["pospal_business_summary"]
    assert biz.description
    assert "营业额" in biz.description or "营业" in biz.description

    sem = tools["pospal_sem_find_products"]
    assert sem.description
    assert "推荐" in sem.description or "名称" in sem.description


def test_semantic_tools_expose_shop_names_param():
    tools = _tool_map()
    schema = tools["pospal_sem_find_products"].parameters
    props = schema.get("properties", {})
    assert "shop_names" in props
    shop_desc = props["shop_names"].get("description", "")
    assert shop_desc
