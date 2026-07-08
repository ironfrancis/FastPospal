from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastpospal.builders import (
    customer_for_update,
    new_customer_payload,
    new_product_payload,
    product_for_update,
)
from fastpospal.client import PospalClient
from fastpospal.parsers import (
    parse_customer_rows,
    parse_html_table,
    parse_product_rows,
    parse_ticket_rows,
)


class PospalService:
    """银豹业务 API 封装。"""

    def __init__(self, client: PospalClient) -> None:
        self.client = client

    # ── 分类 ──────────────────────────────────────────────

    def list_categories(self, user_id: int | None = None) -> list[dict[str, Any]]:
        uid = user_id or self.client.user_id
        result = self.client.ajax("/Category/LoadCategoryDDLJson", {"userId": uid})
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "加载分类失败")
        return result.get("categorys") or []

    def create_category(
        self,
        name: str,
        *,
        parent_name: str = "",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        cat_uid = self.client.ajax("/Category/CreateCategoryUid", {})
        if not cat_uid.get("successed"):
            raise RuntimeError(cat_uid.get("msg") or "生成分类 UID 失败")
        result = self.client.ajax(
            "/Category/AddNewCategory",
            {
                "userId": uid,
                "uid": cat_uid["uid"],
                "parentCategoryName": parent_name,
                "categoryName": name,
                "categoryType": "",
                "mnemonicCode": "",
                "getSyncStores": "true",
            },
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "创建分类失败")
        return result

    def update_category(
        self,
        category_uid: str,
        new_name: str,
        *,
        parent_name: str = "",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        result = self.client.ajax(
            "/Category/Update",
            {
                "userId": uid,
                "categoryUid": category_uid,
                "newCategoryName": new_name,
                "parentCategoryName": parent_name,
                "mnemonicCode": "",
                "getSyncStores": "true",
            },
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "更新分类失败")
        return result

    def delete_categories(
        self,
        category_uids: list[str],
        *,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        result = self.client.ajax(
            "/Category/Delete",
            {
                "userId": uid,
                "categoryUidsJson": json.dumps(category_uids),
                "getSyncStores": "true",
            },
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "删除分类失败")
        return result

    # ── 商品（读） ────────────────────────────────────────

    def product_summary(
        self,
        *,
        keyword: str = "",
        enable: str = "1",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        return self.client.ajax(
            "/Product/LoadProductSummary",
            {
                "groupBySpu": "false",
                "userId": uid,
                "enable": enable,
                "categorysJson": "[]",
                "productTagUidsJson": "[]",
                "keyword": keyword,
            },
        )

    def list_products(
        self,
        *,
        keyword: str = "",
        page_index: int = 1,
        page_size: int = 20,
        enable: str = "1",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        criteria = {
            "groupBySpu": "false",
            "userId": uid,
            "enable": enable,
            "categorysJson": "[]",
            "productTagUidsJson": "[]",
            "keyword": keyword,
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        summary = self.client.ajax("/Product/LoadProductSummary", criteria)
        page = self.client.ajax("/Product/LoadProductsByPage", criteria)
        products = parse_product_rows(page.get("contentView") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "pageIndex": page_index,
            "pageSize": page_size,
            "products": products,
        }

    def get_product(self, product_id: int) -> dict[str, Any]:
        result = self.client.ajax("/Product/FindProduct", {"productId": product_id})
        product = result.get("product")
        if not product:
            raise RuntimeError("商品不存在")
        return product

    def find_product_by_barcode(self, barcode: str) -> dict[str, Any]:
        listed = self.list_products(keyword=barcode, page_size=5)
        for item in listed["products"]:
            if item.get("barcode") == barcode and item.get("productId"):
                return self.get_product(item["productId"])
        if listed["products"]:
            first_id = listed["products"][0].get("productId")
            if first_id:
                return self.get_product(int(first_id))
        raise RuntimeError(f"未找到条码为 {barcode} 的商品")

    def find_product_id_by_barcode(self, barcode: str) -> int | None:
        listed = self.list_products(keyword=barcode, page_size=5)
        for item in listed["products"]:
            if item.get("barcode") == barcode and item.get("productId"):
                return int(item["productId"])
        if listed["products"] and listed["products"][0].get("productId"):
            return int(listed["products"][0]["productId"])
        return None

    # ── 商品（写） ────────────────────────────────────────

    def save_product(self, product: dict[str, Any]) -> dict[str, Any]:
        result = self.client.ajax(
            "/Product/SaveProduct",
            {"productJson": json.dumps(product, ensure_ascii=False)},
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "保存商品失败")
        return result

    def create_product(
        self,
        name: str,
        barcode: str | None = None,
        *,
        category_uid: str | None = None,
        sell_price: str = "9.99",
        buy_price: str = "5.00",
    ) -> dict[str, Any]:
        uid = self.client.user_id
        if not uid:
            raise RuntimeError("未获取到 userId")
        categories = self.list_categories()
        if not categories:
            raise RuntimeError("无可用分类")
        cat = next((c for c in categories if c.get("uid") == category_uid), categories[0])
        bc = barcode or f"MCP{int(time.time())}{uuid.uuid4().hex[:4].upper()}"
        payload = new_product_payload(
            user_id=uid,
            name=name,
            barcode=bc,
            category_uid=str(cat["uid"]),
            category_name=cat.get("name", ""),
            sell_price=sell_price,
            buy_price=buy_price,
        )
        result = self.save_product(payload)
        product_id = self.find_product_id_by_barcode(bc)
        return {
            **result,
            "barcode": bc,
            "productId": product_id,
            "productUid": result.get("productUid"),
        }

    def update_product(self, product_id: int, **changes: Any) -> dict[str, Any]:
        current = self.get_product(product_id)
        payload = product_for_update(current, **changes)
        return self.save_product(payload)

    def delete_product(self, product_id: int) -> dict[str, Any]:
        result = self.client.ajax(
            "/Product/DeleteProduct",
            {"productId": product_id, "getSyncStores": "true"},
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "删除商品失败")
        return result

    # ── 会员（读） ────────────────────────────────────────

    def find_customer(self, number: str) -> dict[str, Any] | None:
        result = self.client.ajax("/Customer/FindCustomer", {"number": number})
        return result.get("customer")

    def list_customers(
        self,
        *,
        keyword: str = "",
        page_index: int = 1,
        page_size: int = 20,
        customer_type: str = "1",
        create_user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = create_user_id if create_user_id is not None else (self.client.user_id or "")
        query = {
            "createUserId": str(uid) if uid else "",
            "categoryUid": "",
            "tagUid": "",
            "type": customer_type,
            "guiderUid": "",
            "keyword": keyword,
        }
        criteria = {
            **query,
            "pageIndex": page_index,
            "pageSize": page_size,
            "orderColumn": "createdDate",
            "asc": "false",
        }
        summary = self.client.ajax("/Customer/LoadCustomerSummary", query)
        page = self.client.ajax("/Customer/LoadCustomersByPage", criteria)
        customers = parse_customer_rows(page.get("contentView") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "summaryView": summary.get("summaryView"),
            "pageIndex": page_index,
            "pageSize": page_size,
            "customers": customers,
        }

    def get_customer_extras(self, number: str) -> dict[str, Any]:
        """会员附属：次卡、权益卡、购物卡、优惠券。"""
        endpoints = {
            "passProducts": "/Customer/LoadCustomerPassProducts",
            "privilegeCards": "/Customer/LoadCustomerPrivilegeCards",
            "shoppingCards": "/Customer/LoadCustomerShoppingCards",
            "couponCodes": "/Customer/LoadCustomerCouponCodes",
        }
        out: dict[str, Any] = {"number": number}
        for key, path in endpoints.items():
            try:
                out[key] = self.client.ajax(path, {"number": number})
            except Exception as exc:  # noqa: BLE001
                out[key] = {"error": str(exc)}
        return out

    # ── 会员（写） ────────────────────────────────────────

    def save_customer(
        self,
        customer: dict[str, Any],
        *,
        original_money: str | float = "0",
        original_point: str | float = "0",
    ) -> dict[str, Any]:
        result = self.client.ajax(
            "/Customer/SaveCustomer",
            {
                "customerJson": json.dumps(customer, ensure_ascii=False),
                "originalMoney": str(original_money),
                "originalPoint": str(original_point),
            },
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "保存会员失败")
        return result

    def create_customer(
        self,
        number: str,
        name: str,
        *,
        tel: str = "",
        remarks: str = "",
    ) -> dict[str, Any]:
        payload = new_customer_payload(number=number, name=name, tel=tel, remarks=remarks)
        return self.save_customer(payload)

    def update_customer(self, number: str, **changes: Any) -> dict[str, Any]:
        current = self.find_customer(number)
        if not current:
            raise RuntimeError(f"会员 {number} 不存在")
        payload = customer_for_update(current, **changes)
        return self.save_customer(
            payload,
            original_money=current.get("money", 0),
            original_point=current.get("point", 0),
        )

    def delete_customer(self, number: str) -> dict[str, Any]:
        result = self.client.ajax("/Customer/DeleteCustomer", {"number": number})
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "删除会员失败")
        return result

    # ── 库存 / 货流（读） ─────────────────────────────────

    def list_stock(
        self,
        *,
        keyword: str = "",
        page_index: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        criteria = {
            "groupByArtNo": "false",
            "mulUserIds": json.dumps([uid]),
            "enable": "1",
            "categorysJson": "[]",
            "productTagUidsJson": "[]",
            "keyword": keyword,
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        summary = self.client.ajax("/Inventory/LoadStockCountSummary", criteria)
        page = self.client.ajax("/Inventory/LoadStockCountByPage", criteria)
        items = parse_html_table(page.get("contentView") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "pageIndex": page_index,
            "pageSize": page_size,
            "items": items,
        }

    def stock_change_history(
        self,
        barcode: str,
        *,
        begin_time: str,
        end_time: str,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        return self.client.ajax(
            "/Inventory/LoadStockChangeHistory",
            {
                "userId": uid,
                "barcode": barcode,
                "beginDateTime": begin_time,
                "endDateTime": end_time,
                "changeType": "",
            },
        )

    def list_stock_flows(
        self,
        *,
        begin_time: str,
        end_time: str,
        page_index: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        criteria: dict[str, Any] = {
            "stockFlowType": "",
            "stockFlowState": "",
            "supplierUid": "",
            "cashierUid": "",
            "timeType": "0",
            "beginTime": begin_time,
            "endTime": end_time,
            "sn": "",
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        form: list[tuple[str, str]] = [(k, str(v)) for k, v in criteria.items()]
        form.append(("userId", str(uid)))
        summary = self.client.ajax_form("/StockFlow/LoadStockFlowSummary", form)
        page = self.client.ajax_form("/StockFlow/LoadStockFlowByPage", form)
        flows = parse_html_table(page.get("contentView") or page.get("view") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "pageIndex": page_index,
            "pageSize": page_size,
            "flows": flows,
        }

    def set_product_stock_limit(
        self,
        product_uid: str,
        *,
        min_stock: float = 0,
        max_stock: float = 999,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        products = [
            {
                "uid": product_uid,
                "minStock": min_stock,
                "maxStock": max_stock,
            }
        ]
        result = self.client.ajax(
            "/Product/SaveProductStockLimit",
            {
                "assignUserIds": json.dumps([uid]),
                "products": json.dumps(products),
            },
        )
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "设置库存上下限失败")
        return result

    # ── 供应商 ────────────────────────────────────────────

    def list_suppliers(self, user_id: int | None = None) -> list[dict[str, Any]]:
        uid = user_id or self.client.user_id
        result = self.client.ajax("/Supplier/LoadSupplierDDLJson", {"userId": uid})
        if not result.get("successed"):
            raise RuntimeError(result.get("msg") or "加载供应商失败")
        raw = result.get("suppliersJson") or "[]"
        return json.loads(raw) if isinstance(raw, str) else raw

    # ── 销售单据 ──────────────────────────────────────────

    def list_tickets(
        self,
        *,
        begin_time: str,
        end_time: str,
        sn: str = "",
        ticket_type: str = "0",
        page_index: int = 1,
        page_size: int = 20,
        user_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        uid = self.client.user_id
        ids = user_ids or ([uid] if uid else [])
        criteria: dict[str, Any] = {
            "sn": sn,
            "beginTime": begin_time,
            "endTime": end_time,
            "cashierUid": "",
            "guiderUid": "",
            "tableUids": "[]",
            "ticketTagUids": "",
            "reversed": ticket_type,
            "onlyCustomer": "false",
            "onlyWholesale": "false",
            "onlyReturn": "false",
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        form: list[tuple[str, str]] = [(k, str(v)) for k, v in criteria.items()]
        for store_id in ids:
            form.append(("userIds", str(store_id)))

        self.client.ensure_login()
        summary = self.client.ajax_form("/Report/LoadTicketSummary", form)
        page = self.client.ajax_form("/Report/LoadTicketsByPage", form)
        tickets = parse_ticket_rows(page.get("contentView") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "summaryView": summary.get("summaryView"),
            "pageIndex": page_index,
            "pageSize": page_size,
            "tickets": tickets,
        }

    # ── 网单 / 采购 ───────────────────────────────────────

    def list_eshop_orders(
        self,
        *,
        begin_time: str,
        end_time: str,
        keyword: str = "",
        page_index: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        criteria: dict[str, Any] = {
            "keyword": keyword,
            "orderState": "",
            "orderSource": "",
            "timeType": "0",
            "beginTime": begin_time,
            "endTime": end_time,
            "paymentMethod": "",
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        form: list[tuple[str, str]] = [(k, str(v)) for k, v in criteria.items()]
        form.append(("userIds", str(uid)))
        summary = self.client.ajax_form("/EshopOrder/LoadOrderSummary", form)
        page = self.client.ajax_form("/EshopOrder/LoadOrdersByPage", form)
        orders = parse_html_table(page.get("contentView") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "pageIndex": page_index,
            "pageSize": page_size,
            "orders": orders,
        }

    def list_product_purchases(
        self,
        *,
        begin_time: str,
        end_time: str,
        keyword: str = "",
        page_index: int = 1,
        page_size: int = 20,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        uid = user_id or self.client.user_id
        criteria = {
            "userId": uid,
            "cashierUid": "",
            "supplierUid": "",
            "payStatus": "",
            "status": "",
            "timeType": "0",
            "beginDatetime": begin_time,
            "endDatetime": end_time,
            "keyword": keyword,
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        summary = self.client.ajax("/ProductPurchase/LoadProductPurchaseSummary", criteria)
        page = self.client.ajax("/ProductPurchase/LoadProductPurchaseByPage", criteria)
        purchases = parse_html_table(page.get("contentView") or "")
        return {
            "successed": summary.get("successed") and page.get("successed"),
            "totalRecord": summary.get("totalRecord", 0),
            "pageIndex": page_index,
            "pageSize": page_size,
            "purchases": purchases,
        }
