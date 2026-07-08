"""HTML 解析器单元测试（离线 fixture，不依赖网络）。"""
from __future__ import annotations

import pytest

from fastpospal.parsers import (
    parse_business_summary_view,
    parse_customer_rows,
    parse_html_table,
    parse_product_rows,
    parse_stock_change_rows,
    parse_summary_span,
    parse_ticket_rows,
)

# ── Fixtures ──────────────────────────────────────────────

PRODUCT_TABLE = """
<table><thead><tr>
  <th>序号</th><th>操作</th><th data="productImage">图片</th>
  <th data="name">名称</th><th data="barcode">条码</th><th data="sellPrice">售价</th>
</tr></thead><tbody>
  <tr data="123" data-uid="uid-abc">
    <td>1</td><td>编辑</td><td></td><td>测试商品</td><td>690001</td><td>9.99</td>
  </tr>
</tbody></table>
"""

CUSTOMER_TABLE = """
<table><thead><tr>
  <th>序号</th><th>操作</th><th data="external">external</th>
  <th data="number">number</th><th data="name">name</th><th data="tel">tel</th>
  <th data="categoryName">categoryName</th><th data="money">money</th>
</tr></thead><tbody>
  <tr data="999" data-uid="cuid-1">
    <td>1</td><td>编辑</td><td>999</td><td>13800138000</td><td>张三</td>
    <td>13800138000</td><td>普通会员</td><td>100.00</td>
  </tr>
</tbody></table>
"""

GENERIC_TABLE = """
<table><thead><tr>
  <th></th><th>序号</th><th>操作</th><th data="sfNo">sfNo</th>
  <th data="orderNumber">orderNumber</th><th data="stockflowType">stockflowType</th>
  <th data="createdDateTime">createdDateTime</th>
</tr></thead><tbody>
  <tr data="7787131">
    <td></td><td>1</td><td>详细</td><td>SF001</td><td>20260708174108</td>
    <td>进货单</td><td>2026-07-08 17:41:08</td>
  </tr>
</tbody></table>
"""

PRODUCT_SALE_TABLE = """
<table><thead><tr>
  <th></th><th>流水号</th><th>销售时间</th><th>销售门店</th>
  <th data="productName">productName</th><th data="barcode">barcode</th>
</tr></thead><tbody>
  <tr data="202607082106293060001">
    <td>1</td><td>202607082106293060001</td><td>2026-07-08 21:06:33</td>
    <td>萌萌书店</td><td>测试商品</td><td>690001</td>
  </tr>
</tbody></table>
"""

EMPTY_TABLE = """
<table><thead><tr><th>序号</th><th>操作</th><th>单号</th></tr></thead>
<tbody><tr><td colspan="10">未查询到符合条件的记录</td></tr></tbody></table>
"""

STOCK_CHANGE_TABLE = """
<table>
<thead><tr>
  <th>序号</th><th>操作时间</th><th>操作人</th>
  <th>变动类型</th><th>库存变动</th><th>校正库存</th><th>备注</th>
</tr></thead>
<tbody>
  <tr><td>1</td><td>2026-07-08 10:00:00</td><td>雪</td>
      <td>销售</td><td>-1</td><td>10</td><td></td></tr>
</tbody></table>
"""

STOCK_CHANGE_EMPTY = """
<thead><tr><th>序号</th><th>操作时间</th></tr></thead>
<tbody><tr><td colspan="10">未找到商品库存变动记录！</td></tr></tbody>
"""


# ── Tests ───────────────────────────────────────────────

class TestParseProductRows:
    def test_basic_fields(self) -> None:
        rows = parse_product_rows(PRODUCT_TABLE)
        assert len(rows) == 1
        assert rows[0]["productId"] == 123
        assert rows[0]["name"] == "测试商品"
        assert rows[0]["barcode"] == "690001"
        assert rows[0]["sellPrice"] == "9.99"

    def test_skips_operation_column(self) -> None:
        rows = parse_product_rows(PRODUCT_TABLE)
        assert "操作" not in rows[0]
        assert "序号" not in rows[0]


class TestParseCustomerRows:
    def test_column_alignment(self) -> None:
        rows = parse_customer_rows(CUSTOMER_TABLE)
        assert len(rows) == 1
        r = rows[0]
        assert r["customerId"] == 999
        assert r["number"] == "13800138000"
        assert r["name"] == "张三"
        assert r["tel"] == "13800138000"
        assert r["categoryName"] == "普通会员"
        assert r["money"] == "100.00"

    def test_no_operation_in_values(self) -> None:
        rows = parse_customer_rows(CUSTOMER_TABLE)
        assert rows[0].get("操作") != "编辑"


class TestParseHtmlTable:
    def test_column_alignment(self) -> None:
        rows = parse_html_table(GENERIC_TABLE)
        assert len(rows) == 1
        r = rows[0]
        assert r["id"] == "7787131"
        assert r["sfNo"] == "SF001"
        assert r["orderNumber"] == "20260708174108"
        assert r["stockflowType"] == "进货单"
        assert r["createdDateTime"] == "2026-07-08 17:41:08"

    def test_empty_placeholder_returns_empty_list(self) -> None:
        rows = parse_html_table(EMPTY_TABLE)
        assert rows == []

    def test_product_sale_single_skip(self) -> None:
        rows = parse_html_table(PRODUCT_SALE_TABLE)
        assert len(rows) == 1
        assert rows[0]["销售时间"] == "2026-07-08 21:06:33"
        assert rows[0]["销售门店"] == "萌萌书店"
        assert rows[0]["productName"] == "测试商品"


class TestParseTicketRows:
    def test_empty_placeholder_returns_empty_list(self) -> None:
        rows = parse_ticket_rows(EMPTY_TABLE)
        assert rows == []


class TestParseStockChangeRows:
    def test_basic(self) -> None:
        rows = parse_stock_change_rows(STOCK_CHANGE_TABLE)
        assert len(rows) == 1
        assert rows[0]["操作时间"] == "2026-07-08 10:00:00"
        assert rows[0]["变动类型"] == "销售"
        assert rows[0]["库存变动"] == "-1"

    def test_empty_returns_empty_list(self) -> None:
        rows = parse_stock_change_rows(STOCK_CHANGE_EMPTY)
        assert rows == []


class TestParseSummarySpan:
    def test_key_value_pairs(self) -> None:
        html = "<span>会员数：1616, 充值金额：20482.93, 总积分：920215.08</span>"
        result = parse_summary_span(html)
        assert result.get("会员数") == "1616"
        assert result.get("充值金额") == "20482.93"
        assert result.get("总积分") == "920215.08"


class TestParseBusinessSummaryView:
    def test_metrics(self) -> None:
        html = """
        <ul><li class="bussinessItem">
          <p class="blue">1702.82</p><div class="subtitle">营业实收(元)</div>
        </li></ul>"""
        result = parse_business_summary_view(html)
        assert result.get("营业实收") == "1702.82"
