from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

_SKIP_HEADER_LABELS = frozenset({"序号", "操作"})
_EMPTY_PLACEHOLDER_MARKERS = ("未查询到", "未找到")


def _is_empty_placeholder_row(tr: Tag) -> bool:
    tds = tr.select("td")
    if len(tds) != 1:
        return False
    td = tds[0]
    text = td.get_text(strip=True)
    if td.get("colspan"):
        return True
    return any(marker in text for marker in _EMPTY_PLACEHOLDER_MARKERS)


def _parse_table_headers(
    soup: BeautifulSoup,
    *,
    skip_labels: frozenset[str] = _SKIP_HEADER_LABELS,
) -> list[str]:
    headers: list[str] = []
    for th in soup.select("thead th"):
        label = th.get("data") or th.get_text(strip=True)
        if label and label not in skip_labels:
            headers.append(label)
    return headers


def _count_leading_skip_columns(soup: BeautifulSoup) -> int:
    """根据 thead 前导空列/序号/操作列，推断 tbody 应跳过的 td 数。"""
    skip = 0
    for th in soup.select("thead th"):
        label = th.get("data") or th.get_text(strip=True)
        if not label or label in _SKIP_HEADER_LABELS:
            skip += 1
        else:
            break
    return skip


def _parse_table_cells(tr: Tag, skip_leading: int = 2) -> list[str]:
    cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
    return cells[skip_leading:] if len(cells) > skip_leading else cells


def _map_cells_to_row(
    headers: list[str],
    cells: list[str],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = dict(extra or {})
    for idx, value in enumerate(cells):
        key = headers[idx] if idx < len(headers) else f"col_{idx}"
        item[key] = value
    return item


def parse_product_rows(content_view: str) -> list[dict[str, Any]]:
    """解析 /Product/LoadProductsByPage 返回的 HTML 表格。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers = _parse_table_headers(soup)
    skip_leading = _count_leading_skip_columns(soup)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        if _is_empty_placeholder_row(tr):
            continue
        product_id = tr.get("data")
        uid = tr.get("data-uid")
        if not product_id:
            continue
        values = _parse_table_cells(tr, skip_leading=skip_leading)
        item: dict[str, Any] = {
            "productId": int(product_id),
            "uid": uid,
        }
        for idx, value in enumerate(values):
            if idx < len(headers):
                item[headers[idx]] = value
        rows.append(item)
    return rows


def parse_ticket_rows(content_view: str) -> list[dict[str, Any]]:
    """解析 /Report/LoadTicketsByPage 返回的 HTML 表格。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers = _parse_table_headers(soup)
    skip_leading = _count_leading_skip_columns(soup)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        if _is_empty_placeholder_row(tr):
            continue
        ticket_id = tr.get("data") or tr.get("data-id")
        cells = _parse_table_cells(tr, skip_leading=skip_leading)
        if not cells:
            continue
        item: dict[str, Any] = {}
        if ticket_id:
            item["ticketId"] = ticket_id
        for idx, value in enumerate(cells):
            key = headers[idx] if idx < len(headers) else f"col_{idx}"
            item[key] = value
        rows.append(item)
    return rows


def parse_customer_rows(content_view: str) -> list[dict[str, Any]]:
    """解析 /Customer/LoadCustomersByPage 返回的 HTML 表格。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers = _parse_table_headers(soup)
    skip_leading = _count_leading_skip_columns(soup)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        if _is_empty_placeholder_row(tr):
            continue
        customer_id = tr.get("data")
        uid = tr.get("data-uid")
        cells = _parse_table_cells(tr, skip_leading=skip_leading)
        if not cells:
            continue
        item: dict[str, Any] = {}
        if customer_id:
            item["customerId"] = int(customer_id)
        if uid:
            item["uid"] = uid
        for idx, value in enumerate(cells):
            if idx < len(headers):
                item[headers[idx]] = value
        rows.append(item)
    return rows


def parse_html_table(content_view: str) -> list[dict[str, Any]]:
    """通用 HTML 表格解析（库存、货流、网单等列表页）。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers = _parse_table_headers(soup)
    skip_leading = _count_leading_skip_columns(soup)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        if _is_empty_placeholder_row(tr):
            continue
        row_id = tr.get("data") or tr.get("data-id") or tr.get("data-uid")
        cells = _parse_table_cells(tr, skip_leading=skip_leading)
        if not cells:
            continue
        item: dict[str, Any] = {}
        if row_id:
            item["id"] = row_id
        for idx, value in enumerate(cells):
            key = headers[idx] if idx < len(headers) else f"col_{idx}"
            item[key] = value
        rows.append(item)
    return rows


def parse_stock_change_rows(content_view: str) -> list[dict[str, Any]]:
    """解析商品库存变动历史 HTML 表格。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers = _parse_table_headers(soup, skip_labels=frozenset({"序号"}))

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        if _is_empty_placeholder_row(tr):
            continue
        cells = _parse_table_cells(tr, skip_leading=1)
        if not cells:
            continue
        rows.append(_map_cells_to_row(headers, cells))
    return rows


def extract_product_id_from_html(content_view: str) -> int | None:
    match = re.search(r'data="(\d+)"\s+data-uid=', content_view)
    if match:
        return int(match.group(1))
    return None


def _normalize_metric_label(label: str) -> str:
    label = re.sub(r"\(.*$", "", label).strip()
    return label


def parse_business_summary_view(view: str) -> dict[str, str]:
    """解析 Dashboard /LoadBusinessSummary 返回的 HTML 指标卡片。"""
    soup = BeautifulSoup(view, "html.parser")
    metrics: dict[str, str] = {}
    for item in soup.select("li.bussinessItem-percent, li.bussinessItem"):
        value_el = item.select_one("p.blue")
        label_el = item.select_one(".subtitle")
        if value_el and label_el:
            label = _normalize_metric_label(label_el.get_text(strip=True))
            if label:
                metrics[label] = value_el.get_text(strip=True)
        for bar in item.select(".percentBar"):
            left_el = bar.select_one(".percentBar__top-left")
            right_el = bar.select_one(".percentBar__top-right")
            if not left_el or not right_el:
                continue
            label = _normalize_metric_label(left_el.get_text(strip=True))
            if label:
                metrics[label] = right_el.get_text(strip=True)
    return metrics


def parse_summary_span(summary_view: str) -> dict[str, str]:
    """解析 summaryView 中的「键：值」汇总文本（如商品销售明细）。"""
    text = BeautifulSoup(summary_view, "html.parser").get_text(" ", strip=True)
    metrics: dict[str, str] = {}
    for match in re.finditer(r"([^，,：:]+)[：:]\s*([\d.]+%?)", text):
        key = match.group(1).strip()
        key = re.sub(r"^[（(\s]+", "", key).strip()
        key = re.sub(r"[\s）)]+$", "", key).strip()
        if key:
            metrics[key] = match.group(2).strip()
    return metrics
