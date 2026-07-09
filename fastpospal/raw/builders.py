from __future__ import annotations

import json
from datetime import date
from typing import Any


def new_product_payload(
    *,
    user_id: int,
    name: str,
    barcode: str,
    category_uid: str,
    category_name: str,
    sell_price: str = "0.00",
    buy_price: str = "0.00",
    stock: str = "0",
    enable: str = "1",
) -> dict[str, Any]:
    """构造 SaveProduct 新建商品 JSON（图书/零售通用最小字段）。"""
    return {
        "id": 0,
        "enable": enable,
        "userId": user_id,
        "barcode": barcode,
        "name": name,
        "categoryUid": category_uid,
        "categoryName": category_name,
        "sellPrice": sell_price,
        "buyPrice": buy_price,
        "isCustomerDiscount": "1",
        "customerPrice": sell_price,
        "sellPrice2": "0.00",
        "pinyin": "",
        "supplierUid": None,
        "supplierName": "无",
        "supplierRangeList": [],
        "noStock": 0,
        "stock": stock,
        "attribute1": "",
        "attribute2": "",
        "attribute3": "",
        "attribute4": "",
        "attribute6": "",
        "productimages": [],
        "productTags": [],
        "customerPrices": [],
        "productUnitExchangeList": [],
    }


def product_for_update(product: dict[str, Any], **changes: Any) -> dict[str, Any]:
    """基于 FindProduct 结果合并更新字段，补齐 SaveProduct 必填空字段。"""
    merged = dict(product)
    merged.update(changes)
    for key in (
        "attribute1",
        "attribute2",
        "attribute3",
        "attribute4",
        "attribute6",
        "productimages",
        "productTags",
        "customerPrices",
        "productUnitExchangeList",
    ):
        if key not in merged or merged[key] is None:
            merged[key] = [] if key != "attribute6" else ""
    if merged.get("supplierRangeList") is None:
        merged["supplierRangeList"] = []
    return merged


def new_customer_payload(
    *,
    number: str,
    name: str,
    tel: str = "",
    remarks: str = "",
) -> dict[str, Any]:
    today = date.today().isoformat()
    return {
        "id": 0,
        "enable": "1",
        "number": number,
        "name": name,
        "customerCategoryUid": "",
        "categoryName": "",
        "discount": 100,
        "money": "0",
        "point": "0",
        "tel": tel,
        "password": "",
        "birthday": "",
        "createdDate": today,
        "expiryDate": "",
        "credit": "0",
        "qq": "",
        "email": "",
        "remarks": remarks,
        "departmentTagUid": "",
        "departmentTagName": "-",
        "subsidyAmount": "",
        "customerExt": {"sex": None},
    }


def customer_for_update(customer: dict[str, Any], **changes: Any) -> dict[str, Any]:
    merged = dict(customer)
    merged.update(changes)
    if "customerExt" not in merged or merged["customerExt"] is None:
        merged["customerExt"] = {"sex": None}
    return merged
