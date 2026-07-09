from __future__ import annotations

from typing import Any

from fastpospal.raw.service import PospalService

from fastpospal.semantic.categories import (
    build_categorys_json,
    flatten_categories,
    match_categories_by_keyword,
    parse_money_cell,
    pick_sales_amount_column,
    resolve_category_id,
)
from fastpospal.semantic.datetime_range import days_ago_range, resolve_date_range
from fastpospal.semantic.formatters import compact_rows, fail, ok
from fastpospal.semantic.shops import resolve_shop_id


class PospalSemanticService:
    """银豹语义层：面向 Agent 的业务友好接口。"""

    def __init__(self, raw: PospalService) -> None:
        self.raw = raw

    def _categories(self, shop_names: str | None) -> list[dict[str, str]]:
        user_id = resolve_shop_id(shop_names)
        nodes = self.raw.list_categories(user_id=user_id)
        return flatten_categories(nodes)

    def find_products(
        self,
        keyword: str,
        *,
        limit: int = 5,
        shop_names: str | None = None,
    ) -> dict[str, Any]:
        user_id = resolve_shop_id(shop_names)
        result = self.raw.list_products(
            keyword=keyword,
            page_index=1,
            page_size=min(max(limit, 1), 50),
            user_id=user_id,
        )
        products = (result.get("products") or [])[:limit]
        return ok({"products": products, "total": result.get("totalRecord", len(products))})

    def check_product_stock(
        self,
        keyword: str,
        *,
        shop_names: str | None = None,
    ) -> dict[str, Any]:
        if not keyword.strip():
            return fail("请提供商品名称或条码（keyword 参数）")
        user_id = resolve_shop_id(shop_names)
        listed = self.raw.list_products(
            keyword=keyword,
            page_index=1,
            page_size=5,
            user_id=user_id,
        )
        products = listed.get("products") or []
        if not products:
            return fail(f"未找到与「{keyword}」匹配的商品")
        product = products[0]
        stock = product.get("stock") or product.get("现有库存")
        return ok(
            {
                "product_name": product.get("name") or product.get("商品名称"),
                "barcode": product.get("barcode") or product.get("商品条码"),
                "stock": stock,
                "raw": product,
            }
        )

    def get_product_categories_json(
        self,
        *,
        search: str = "",
        limit: int = 120,
        shop_names: str | None = None,
    ) -> dict[str, Any]:
        rows = self._categories(shop_names)
        key = search.strip().lower()
        if key:
            rows = [
                row
                for row in rows
                if key in row.get("name", "").lower()
                or key in row.get("parent_name", "").lower()
            ]
        limit = max(1, min(500, limit))
        total = len(rows)
        slice_rows = rows[:limit]
        payload: dict[str, Any] = {
            "category_json": slice_rows,
            "total": total,
            "returned": len(slice_rows),
        }
        if total > limit:
            payload["note"] = (
                f"共 {total} 条分类，仅返回前 {limit} 条；"
                "请使用 search 缩小范围。"
            )
        return ok(payload)

    def query_category_sales(
        self,
        category_name: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        shop_names: str | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        begin, end = resolve_date_range(start_date, end_date)
        user_id = resolve_shop_id(shop_names)
        categories = self._categories(shop_names)
        matches = match_categories_by_keyword(categories, category_name)
        categorys_json = "[]"
        if len(matches) > 1:
            return fail(
                "ambiguous_category",
                data={
                    "category_candidates": matches[:10],
                    "summary": {
                        "note": "匹配到多个分类，请使用 category_id 指定其一。"
                    },
                },
            )
        if len(matches) == 1:
            categorys_json = build_categorys_json([matches[0]["id"]])
        elif categories:
            category_id = resolve_category_id(categories, category_name)
            if category_id:
                categorys_json = build_categorys_json([category_id])

        result = self.raw.list_product_sale_by_page(
            begin_datetime=begin,
            end_datetime=end,
            keyword=category_name if categorys_json == "[]" else "",
            categorys_json=categorys_json,
            page_size=10000,
            user_id=user_id,
        )
        return self._aggregate_sale_items(result.get("items") or [], limit=limit)

    def get_store_sales_summary(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        shop_names: str | None = None,
    ) -> dict[str, Any]:
        begin, end = resolve_date_range(start_date, end_date)
        user_id = resolve_shop_id(shop_names)
        result = self.raw.business_summary(
            begin_datetime=begin,
            end_datetime=end,
            user_id=user_id,
        )
        metrics = result.get("metrics") or {}
        return ok(
            {
                "metrics": metrics,
                "store_name": result.get("store_name"),
                "begin_datetime": begin,
                "end_datetime": end,
            }
        )

    def query_sales_detail(
        self,
        *,
        search: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        shop_names: str | None = None,
        page: int = 1,
        size: int = 20,
        compact: bool = False,
    ) -> dict[str, Any]:
        begin, end = resolve_date_range(start_date, end_date)
        user_id = resolve_shop_id(shop_names)
        result = self.raw.product_sale_summary(
            begin_datetime=begin,
            end_datetime=end,
            page_index=max(1, page),
            page_size=min(max(1, size), 100),
            user_id=user_id,
        )
        items = result.get("items") or []
        if search:
            key = search.lower()
            items = [
                row
                for row in items
                if any(key in str(value).lower() for value in row.values())
            ]
        payload: dict[str, Any] = {
            "total": result.get("totalRecord", len(items)),
            "page": page,
            "size": size,
            "summary": result.get("summary"),
            "items": compact_rows(items) if compact else items,
        }
        return ok(payload)

    def query_stock_flows(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        shop_names: str | None = None,
        page: int = 1,
        size: int = 20,
        compact: bool = False,
    ) -> dict[str, Any]:
        begin, end = resolve_date_range(start_date, end_date)
        user_id = resolve_shop_id(shop_names)
        result = self.raw.list_stock_flows(
            begin_time=begin,
            end_time=end,
            page_index=max(1, page),
            page_size=min(max(1, size), 100),
            user_id=user_id,
        )
        items = result.get("items") or result.get("flows") or []
        payload = {
            "total": result.get("totalRecord", len(items)),
            "page": page,
            "size": size,
            "items": compact_rows(items) if compact else items,
        }
        return ok(payload)

    def list_products_admin(
        self,
        *,
        page: int = 1,
        size: int = 20,
        keyword: str = "",
        shop_names: str | None = None,
        compact: bool = False,
    ) -> dict[str, Any]:
        user_id = resolve_shop_id(shop_names)
        result = self.raw.list_products(
            keyword=keyword,
            page_index=max(1, page),
            page_size=min(max(1, size), 100),
            user_id=user_id,
        )
        products = result.get("products") or []
        payload = {
            "total": result.get("totalRecord", len(products)),
            "page": page,
            "size": size,
            "products": compact_rows(products) if compact else products,
        }
        return ok(payload)

    def analyze_restock_needs(
        self,
        *,
        days: int = 3,
        shop_names: str | None = None,
        hot_threshold: float = 0.5,
        urgent_threshold: float = 0.8,
        sold_out_threshold: float = 1.0,
    ) -> dict[str, Any]:
        begin, end = days_ago_range(days)
        user_id = resolve_shop_id(shop_names)
        sale_result = self.raw.list_product_sale_by_page(
            begin_datetime=begin,
            end_datetime=end,
            page_size=10000,
            user_id=user_id,
        )
        items = sale_result.get("items") or []
        hot: list[dict[str, Any]] = []
        urgent: list[dict[str, Any]] = []
        sold_out: list[dict[str, Any]] = []
        skipped_no_inventory = 0

        for row in items:
            name = row.get("商品名称") or row.get("name") or ""
            stock_raw = row.get("现有库存") or row.get("stock") or "0"
            stock_text = str(stock_raw).strip().replace("－", "-")
            if stock_text in {"", "-", "--"}:
                skipped_no_inventory += 1
                continue
            try:
                stock = float(stock_text)
            except ValueError:
                stock = 0.0
            try:
                sold = float(row.get("销售数量") or 0)
            except (TypeError, ValueError):
                sold = 0.0
            if stock <= 0:
                ratio = sold_out_threshold + 1 if sold > 0 else 0.0
            else:
                ratio = sold / stock
            entry = {
                "product_name": name,
                "shop_name": shop_names or "关天培店",
                "current_stock": stock,
                "sold_quantity": sold,
                "sales_ratio": round(ratio, 3),
                "daily_avg_sales": round(sold / max(days, 1), 2),
                "recommended_restock": max(0, int(sold - stock)),
            }
            if ratio >= sold_out_threshold:
                sold_out.append(entry)
            elif ratio >= urgent_threshold:
                urgent.append(entry)
            elif ratio >= hot_threshold:
                hot.append(entry)

        return ok(
            {
                "hot_products": hot,
                "urgent_products": urgent,
                "sold_out_products": sold_out,
                "summary": {
                    "days": days,
                    "hot_count": len(hot),
                    "urgent_count": len(urgent),
                    "sold_out_count": len(sold_out),
                    "skipped_no_inventory_count": skipped_no_inventory,
                },
            }
        )

    def _aggregate_sale_items(
        self,
        items: list[dict[str, Any]],
        *,
        limit: int,
    ) -> dict[str, Any]:
        if not items:
            return ok(
                {
                    "summary": {
                        "product_rows": 0,
                        "total_quantity": 0.0,
                        "total_amount": None,
                    },
                    "top_products": [],
                }
            )

        columns = list(items[0].keys())
        qty_col = "销售数量" if "销售数量" in columns else None
        amount_col = pick_sales_amount_column(columns)
        total_quantity = 0.0
        total_amount = None
        if qty_col:
            for row in items:
                try:
                    total_quantity += float(row.get(qty_col) or 0)
                except (TypeError, ValueError):
                    pass
        if amount_col:
            total_amount = sum(parse_money_cell(row.get(amount_col)) for row in items)

        def sort_key(row: dict[str, Any]) -> float:
            if not qty_col:
                return 0.0
            try:
                return float(row.get(qty_col) or 0)
            except (TypeError, ValueError):
                return 0.0

        top_products = sorted(items, key=sort_key, reverse=True)[:limit]
        return ok(
            {
                "summary": {
                    "product_rows": len(items),
                    "total_quantity": total_quantity,
                    "total_amount": total_amount,
                },
                "top_products": top_products,
            }
        )
