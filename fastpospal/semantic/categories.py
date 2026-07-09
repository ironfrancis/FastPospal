from __future__ import annotations

import json
import re
from typing import Any


REPORT_V2_CATEGORY_SENTINEL = -12345


def flatten_categories(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not nodes:
        return []

    if nodes and not any(isinstance(node.get("children"), list) for node in nodes if isinstance(node, dict)):
        uid_to_name = {
            str(node.get("uid") or node.get("txtUid") or node.get("id")): str(node.get("name") or "")
            for node in nodes
            if isinstance(node, dict)
        }
        flat: list[dict[str, str]] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            uid = node.get("uid") or node.get("txtUid") or node.get("id")
            name = node.get("name") or ""
            if not uid or not name:
                continue
            parent_uid = str(node.get("parentUid") or node.get("txtParentUid") or "")
            flat.append(
                {
                    "id": str(uid),
                    "name": str(name),
                    "parent_name": uid_to_name.get(parent_uid, ""),
                }
            )
        return flat

    flat: list[dict[str, str]] = []

    def walk(node: dict[str, Any], parent_name: str = "") -> None:
        uid = node.get("uid") or node.get("txtUid") or node.get("id")
        name = node.get("name") or ""
        if uid and name:
            flat.append(
                {
                    "id": str(uid),
                    "name": str(name),
                    "parent_name": parent_name,
                }
            )
        child_parent = str(name) if name else parent_name
        for child in node.get("children") or []:
            if isinstance(child, dict):
                walk(child, child_parent)

    for node in nodes:
        if isinstance(node, dict):
            walk(node)
    return flat


def build_categorys_json(category_ids: list[str]) -> str:
    ids = [str(item).strip() for item in category_ids if str(item).strip()]
    if not ids:
        return "[]"
    payload: list[Any] = [ids[0], REPORT_V2_CATEGORY_SENTINEL]
    return json.dumps(payload, ensure_ascii=False)


def match_categories_by_keyword(
    categories: list[dict[str, str]],
    keyword: str,
) -> list[dict[str, str]]:
    key = (keyword or "").strip().lower()
    if not key:
        return []
    exact = [item for item in categories if item.get("name", "").lower() == key]
    if exact:
        return exact
    partial = [
        item
        for item in categories
        if key in item.get("name", "").lower()
        or key in item.get("parent_name", "").lower()
    ]
    return partial


def resolve_category_id(
    categories: list[dict[str, str]],
    category_name: str,
) -> str | None:
    matches = match_categories_by_keyword(categories, category_name)
    if len(matches) == 1:
        return matches[0]["id"]
    for item in categories:
        if item.get("name") == category_name:
            return item["id"]
    for item in categories:
        if category_name in item.get("name", ""):
            return item["id"]
    for item in categories:
        if category_name in item.get("parent_name", ""):
            return item["id"]
    return None


def pick_sales_amount_column(columns: list[str]) -> str | None:
    for preferred in ("实收金额", "销售金额", "销售总额", "销售额", "商品总售价"):
        if preferred in columns:
            return preferred
    for column in columns:
        if any(token in column for token in ("占比", "利润率", "率")):
            continue
        if "数量" in column:
            continue
        if any(token in column for token in ("实收金额", "销售金额", "销售总额", "销售额")):
            return column
    return None


def parse_money_cell(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "--"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0
