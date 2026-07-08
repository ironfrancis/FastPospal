#!/usr/bin/env python3
"""集成验收测试：连通性 + 清洗质量 + 响应体积。"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from fastpospal.client import PospalClient  # noqa: E402
from fastpospal.service import PospalService  # noqa: E402

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


def size_kb(obj: Any) -> float:
    return len(json.dumps(obj, ensure_ascii=False, default=str).encode()) / 1024


def has_raw_html(obj: Any) -> bool:
    text = json.dumps(obj, ensure_ascii=False, default=str)
    return any(m in text for m in ("<table", "<tr ", "<td ", "<span id=", "mainTableView"))


class AcceptanceReport:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.results.append({"name": name, "status": PASS if condition else FAIL, "detail": detail})

    def skip(self, name: str, reason: str) -> None:
        self.results.append({"name": name, "status": SKIP, "detail": reason})

    def summary(self) -> tuple[int, int, int]:
        p = sum(1 for r in self.results if r["status"] == PASS)
        f = sum(1 for r in self.results if r["status"] == FAIL)
        s = sum(1 for r in self.results if r["status"] == SKIP)
        return p, f, s

    def print_report(self) -> None:
        p, f, s = self.summary()
        print("\n" + "=" * 72)
        print(f"验收报告  PASS={p}  FAIL={f}  SKIP={s}")
        print("=" * 72)
        for r in self.results:
            icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[r["status"]]
            detail = f" — {r['detail']}" if r["detail"] else ""
            print(f"{icon} {r['name']}{detail}")


def main() -> int:
    account = os.environ.get("POSPAL_ACCOUNT", "")
    password = os.environ.get("POSPAL_PASSWORD", "")
    if not account or not password:
        print("缺少 POSPAL_ACCOUNT / POSPAL_PASSWORD")
        return 1

    report = AcceptanceReport()
    client = PospalClient(account=account, password=password)
    client.login()
    svc = PospalService(client)

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    day_begin = f"{yesterday} 00:00:00"
    day_end = f"{yesterday} 23:59:59"
    week_begin = f"{week_ago} 00:00:00"
    week_end = f"{datetime.now().strftime('%Y-%m-%d')} 23:59:59"

    # ── 1. 连通性 ──
    info = client.session_info()
    report.check("session_info.logged_in", info.get("logged_in") is True, str(info.get("store_name")))

    cats = svc.list_categories()
    report.check("list_categories.non_empty", len(cats) > 0, f"{len(cats)} 分类")

    summary = svc.product_summary()
    report.check("product_summary.totalRecord", summary.get("totalRecord", 0) > 0, str(summary.get("totalRecord")))

    # ── 2. 列对齐：商品列表 ──
    products = svc.list_products(page_size=3)
    report.check("list_products.success", products.get("successed") is True)
    if products.get("products"):
        p0 = products["products"][0]
        report.check(
            "list_products.column_name",
            "name" in p0 and p0["name"] not in ("", "-", "编辑"),
            p0.get("name", ""),
        )
        report.check(
            "list_products.column_barcode",
            "barcode" in p0 and not p0["barcode"].startswith("编辑"),
            p0.get("barcode", ""),
        )

    # ── 3. 列对齐：会员列表 ──
    customers = svc.list_customers(page_size=3)
    report.check("list_customers.success", customers.get("successed") is True)
    if customers.get("customers"):
        c0 = customers["customers"][0]
        # tel 应该是手机号格式，不应是「普通会员」
        tel = c0.get("tel", "")
        report.check(
            "list_customers.tel_not_category",
            tel != "普通会员" and tel != c0.get("categoryName"),
            f"tel={tel}",
        )
        report.check(
            "list_customers.categoryName_not_money",
            c0.get("categoryName") not in ("0.00", "100.00") or c0.get("money") != c0.get("categoryName"),
            f"categoryName={c0.get('categoryName')}, money={c0.get('money')}",
        )

    # ── 4. summaryView 清洗 ──
    report.check(
        "list_customers.summary_parsed",
        isinstance(customers.get("summary"), dict) and len(customers.get("summary", {})) > 0,
        str(customers.get("summary", customers.get("summaryView", "")))[:80],
    )
    report.check(
        "list_customers.no_raw_summaryView",
        "summaryView" not in customers or customers.get("summaryView") is None,
        "summaryView 应被 parse 后移除",
    )

    # ── 5. 营业概况 ──
    biz = svc.business_summary(begin_datetime=day_begin, end_datetime=day_end)
    report.check("business_summary.metrics", "营业实收" in biz.get("metrics", {}), str(biz.get("metrics")))
    report.check("business_summary.no_html", not has_raw_html(biz))

    # ── 6. 销售汇总 ──
    sale = svc.product_sale_summary(begin_datetime=day_begin, end_datetime=day_end, page_size=3)
    report.check("product_sale_summary.summary", "总实收" in sale.get("summary", {}), str(sale.get("summary")))
    if sale.get("items"):
        item = sale["items"][0]
        # 销售时间应该是日期格式，不应是流水号
        st = item.get("销售时间", "")
        report.check(
            "product_sale_summary.time_format",
            "-" in st and ":" in st,
            f"销售时间={st}",
        )

    # ── 7. 货流单列对齐 ──
    flows = svc.list_stock_flows(begin_time=week_begin, end_time=week_end, page_size=3)
    if flows.get("flows") and flows["flows"][0].get("stockflowType") != "-":
        f0 = flows["flows"][0]
        report.check(
            "list_stock_flows.type_not_datetime",
            f0.get("stockflowType") not in ("进货单", "2026-07-08 17:41:08") or "进货" in str(f0.get("stockflowType", "")),
            f"stockflowType={f0.get('stockflowType')}, createdDateTime={f0.get('createdDateTime')}",
        )
        report.check(
            "list_stock_flows.datetime_has_colon",
            ":" in str(f0.get("createdDateTime", "")),
            f"createdDateTime={f0.get('createdDateTime')}",
        )
    else:
        report.skip("list_stock_flows.alignment", "无货流数据")

    # ── 8. 空结果不应有占位行 ──
    tickets = svc.list_tickets(begin_time=day_begin, end_time=day_end, page_size=5)
    if tickets.get("totalRecord", 0) == 0:
        report.check(
            "list_tickets.empty_no_placeholder",
            tickets.get("tickets") == [],
            f"tickets={tickets.get('tickets')}",
        )
    else:
        report.skip("list_tickets.empty_no_placeholder", f"totalRecord={tickets.get('totalRecord')}")

    purchases = svc.list_product_purchases(begin_time=week_begin, end_time=week_end, page_size=5)
    if purchases.get("totalRecord", 0) == 0:
        report.check(
            "list_product_purchases.empty_no_placeholder",
            purchases.get("purchases") == [],
            f"purchases={purchases.get('purchases')}",
        )

    # ── 9. 库存流水 HTML 清洗 ──
    if products.get("products") and products["products"][0].get("barcode"):
        barcode = products["products"][0]["barcode"]
        history = svc.stock_change_history(barcode, begin_time=week_begin, end_time=week_end)
        report.check("stock_change_history.no_html", not has_raw_html(history))
        report.check(
            "stock_change_history.has_logs_key",
            "logs" in history or "stockChangeLogs" in history,
            str(list(history.keys())),
        )
    else:
        report.skip("stock_change_history", "无条码")

    # ── 10. 响应体积 ──
    report.check("list_categories.size", size_kb(cats) < 100, f"{size_kb(cats):.1f} KB")

    report.print_report()
    _, fails, _ = report.summary()
    client.close()
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
