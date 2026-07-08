from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


def parse_product_rows(content_view: str) -> list[dict[str, Any]]:
    """解析 /Product/LoadProductsByPage 返回的 HTML 表格。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers: list[str] = []
    for th in soup.select("thead th"):
        label = th.get("data") or th.get_text(strip=True)
        if label and label not in ("操作",):
            headers.append(label)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        product_id = tr.get("data")
        uid = tr.get("data-uid")
        if not product_id:
            continue
        cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
        # 前两列通常是序号和操作
        values = cells[2:] if len(cells) > 2 else cells
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
    headers: list[str] = []
    for th in soup.select("thead th"):
        label = th.get("data") or th.get_text(strip=True)
        if label:
            headers.append(label)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        ticket_id = tr.get("data") or tr.get("data-id")
        cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
        if not cells:
            continue
        item: dict[str, Any] = {}
        if ticket_id:
            item["ticketId"] = ticket_id
        for idx, value in enumerate(cells):
            if idx < len(headers):
                item[headers[idx]] = value
            else:
                item[f"col_{idx}"] = value
        rows.append(item)
    return rows


def parse_customer_rows(content_view: str) -> list[dict[str, Any]]:
    """解析 /Customer/LoadCustomersByPage 返回的 HTML 表格。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers: list[str] = []
    for th in soup.select("thead th"):
        label = th.get("data") or th.get_text(strip=True)
        if label:
            headers.append(label)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        customer_id = tr.get("data")
        uid = tr.get("data-uid")
        cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
        if not cells:
            continue
        item: dict[str, Any] = {}
        if customer_id:
            item["customerId"] = int(customer_id)
        if uid:
            item["uid"] = uid
        for idx, value in enumerate(cells[2:] if len(cells) > 2 else cells):
            if idx < len(headers):
                item[headers[idx]] = value
        rows.append(item)
    return rows


def parse_html_table(content_view: str) -> list[dict[str, Any]]:
    """通用 HTML 表格解析（库存、货流、网单等列表页）。"""
    soup = BeautifulSoup(content_view, "html.parser")
    headers: list[str] = []
    for th in soup.select("thead th"):
        label = th.get("data") or th.get_text(strip=True)
        if label:
            headers.append(label)

    rows: list[dict[str, Any]] = []
    for tr in soup.select("tbody tr"):
        row_id = tr.get("data") or tr.get("data-id") or tr.get("data-uid")
        cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
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


def extract_product_id_from_html(content_view: str) -> int | None:
    match = re.search(r'data="(\d+)"\s+data-uid=', content_view)
    if match:
        return int(match.group(1))
    return None


def parse_business_summary_view(view: str) -> dict[str, str]:
    """解析 Dashboard /LoadBusinessSummary 返回的 HTML 指标卡片。"""
    soup = BeautifulSoup(view, "html.parser")
    metrics: dict[str, str] = {}
    for item in soup.select("li.bussinessItem-percent, li.bussinessItem"):
        value_el = item.select_one("p.blue")
        label_el = item.select_one(".subtitle")
        if not value_el or not label_el:
            continue
        label = label_el.get_text(strip=True)
        label = re.sub(r"\(.*$", "", label).strip()
        if label:
            metrics[label] = value_el.get_text(strip=True)
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
