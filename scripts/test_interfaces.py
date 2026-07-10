#!/usr/bin/env python3
"""只读接口冒烟测试：可用性 + 长内容清洗/压缩评估。"""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()

from fastpospal.client import PospalClient  # noqa: E402
from fastpospal.service import PospalService  # noqa: E402


def size_kb(obj: Any) -> float:
    return len(json.dumps(obj, ensure_ascii=False, default=str).encode()) / 1024


def has_html(obj: Any) -> bool:
    """检测响应中是否仍含未清洗的 HTML 片段。"""
    text = json.dumps(obj, ensure_ascii=False, default=str)
    markers = ("<table", "<tr", "<td", "<div", "contentView", "summaryView")
    return any(m in text for m in markers)


def sample_keys(obj: Any, max_depth: int = 2) -> list[str]:
    """列出顶层/二层字段，便于评估结构是否精简。"""
    keys: list[str] = []

    def walk(o: Any, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                path = f"{prefix}.{k}" if prefix else k
                keys.append(path)
                walk(v, path, depth + 1)
        elif isinstance(o, list) and o:
            walk(o[0], f"{prefix}[0]", depth + 1)

    walk(obj, "", 0)
    return keys[:30]


def run_test(name: str, fn: Callable[[], Any]) -> dict[str, Any]:
    row: dict[str, Any] = {"name": name, "ok": False}
    try:
        result = fn()
        row["ok"] = True
        row["size_kb"] = round(size_kb(result), 2)
        row["has_html"] = has_html(result)
        row["keys"] = sample_keys(result)
        # 记录关键统计
        if isinstance(result, dict):
            for k in ("totalRecord", "successed", "found", "hint", "metrics", "summary"):
                if k in result:
                    row[k] = result[k]
            for list_key in ("products", "customers", "items", "tickets", "orders", "purchases", "flows"):
                if list_key in result and isinstance(result[list_key], list):
                    row[f"{list_key}_count"] = len(result[list_key])
                    if result[list_key]:
                        row[f"{list_key}_sample"] = result[list_key][0]
        elif isinstance(result, list):
            row["count"] = len(result)
            if result:
                row["sample"] = result[0]
        row["result_preview"] = _preview(result)
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["trace"] = traceback.format_exc().splitlines()[-3:]
    return row


def _preview(obj: Any, max_len: int = 400) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return s[:max_len] + ("…" if len(s) > max_len else "")


def main() -> int:
    import os

    account = os.environ.get("POSPAL_ACCOUNT", "")
    password = os.environ.get("POSPAL_PASSWORD", "")
    if not account or not password:
        print("缺少 POSPAL_ACCOUNT / POSPAL_PASSWORD")
        return 1

    client = PospalClient(account=account, password=password)
    client.login()
    svc = PospalService(client)

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    begin = f"{week_ago} 00:00:00"
    end = f"{today} 23:59:59"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    day_begin = f"{yesterday} 00:00:00"
    day_end = f"{yesterday} 23:59:59"

    tests: list[tuple[str, Callable[[], Any]]] = [
        ("session_info", lambda: client.session_info()),
        ("list_categories", lambda: svc.list_categories()),
        ("product_summary", lambda: svc.product_summary()),
        ("list_products", lambda: svc.list_products(page_size=5)),
        ("list_customers", lambda: svc.list_customers(page_size=5)),
        ("list_stock", lambda: svc.list_stock(page_size=5)),
        ("list_suppliers", lambda: svc.list_suppliers()),
        ("business_summary", lambda: svc.business_summary(begin_datetime=day_begin, end_datetime=day_end)),
        ("recharge_summary", lambda: svc.recharge_summary(begin_datetime=day_begin, end_datetime=day_end)),
        ("product_sale_summary", lambda: svc.product_sale_summary(begin_datetime=day_begin, end_datetime=day_end, page_size=5)),
        ("list_tickets", lambda: svc.list_tickets(begin_time=day_begin, end_time=day_end, page_size=5)),
        ("list_stock_flows", lambda: svc.list_stock_flows(begin_time=begin, end_time=end, page_size=5)),
        ("list_eshop_orders", lambda: svc.list_eshop_orders(begin_time=begin, end_time=end, page_size=5)),
        ("list_product_purchases", lambda: svc.list_product_purchases(begin_time=begin, end_time=end, page_size=5)),
    ]

    # 若有商品，测详情接口
    products = svc.list_products(page_size=1)
    if products.get("products"):
        pid = products["products"][0]["productId"]
        barcode = products["products"][0].get("barcode", "")
        tests.append(("get_product", lambda p=pid: svc.get_product(p)))
        if barcode:
            tests.append(("find_product_by_barcode", lambda b=barcode: svc.find_product_by_barcode(b)))
            tests.append(
                (
                    "stock_change_history",
                    lambda b=barcode: svc.stock_change_history(b, begin_time=begin, end_time=end),
                )
            )

    # 若有会员，测详情
    customers = svc.list_customers(page_size=1)
    if customers.get("customers"):
        number = customers["customers"][0].get("卡号") or customers["customers"][0].get("会员号")
        if number:
            tests.append(("find_customer", lambda n=number: svc.find_customer(n) or {"found": False}))
            tests.append(("get_customer_extras", lambda n=number: svc.get_customer_extras(n)))

    results: list[dict[str, Any]] = []
    for name, fn in tests:
        print(f"Testing {name}...", file=sys.stderr)
        results.append(run_test(name, fn))

    # ── 报告 ──
    ok_count = sum(1 for r in results if r["ok"])
    print("\n" + "=" * 72)
    print(f"接口测试报告  {ok_count}/{len(results)} 通过")
    print("=" * 72)

    for r in results:
        status = "✅" if r["ok"] else "❌"
        line = f"{status} {r['name']}"
        if r["ok"]:
            line += f"  |  {r['size_kb']} KB"
            if r.get("has_html"):
                line += "  |  ⚠️ 含 HTML/原始视图"
            else:
                line += "  |  ✓ 已结构化"
            for k in ("totalRecord", "count", "products_count", "customers_count", "items_count", "tickets_count"):
                if k in r:
                    line += f"  |  {k}={r[k]}"
        else:
            line += f"  |  {r.get('error', 'unknown')}"
        print(line)

    print("\n" + "-" * 72)
    print("长内容清洗/压缩分析")
    print("-" * 72)

    html_leaks = [r["name"] for r in results if r.get("has_html")]
    large = [(r["name"], r["size_kb"]) for r in results if r.get("size_kb", 0) > 10]

    print(f"• HTML 解析清洗：parsers.py 将 contentView HTML 表格 → 结构化 dict")
    print(f"• 营业概况/销售汇总：HTML 卡片/span → metrics/summary 键值对")
    if html_leaks:
        print(f"• ⚠️ 仍含 HTML/原始字段的接口：{', '.join(html_leaks)}")
    else:
        print("• ✓ 所有测试接口均无 HTML 泄漏")

    if large:
        print("• 响应较大的接口（>10KB，无压缩截断）：")
        for name, kb in sorted(large, key=lambda x: -x[1]):
            print(f"    - {name}: {kb} KB")
    else:
        print("• 所有接口响应均 <10KB（page_size=5 条件下）")

    # get_product / find_customer 原始 JSON 体积对比
    for r in results:
        if r["name"] == "get_product" and r.get("ok"):
            raw_keys = len(r.get("keys", []))
            print(f"• get_product 字段数（含嵌套）≈ {raw_keys}，返回银豹完整商品 JSON，未做字段裁剪")

    for r in results:
        if r["name"] == "get_customer_extras" and r.get("ok"):
            print(f"• get_customer_extras: {r['size_kb']} KB — 4 个子接口原始响应，未清洗/压缩")

    print("\n" + "-" * 72)
    print("实用性评估")
    print("-" * 72)
    notes = {
        "session_info": "会话诊断，Agent 排查登录问题必备",
        "list_categories": "分类树，创建商品前置依赖",
        "product_summary": "轻量统计，适合「有多少商品」类问题",
        "list_products": "分页列表，HTML→结构化，实用",
        "get_product": "完整详情，字段多但精确",
        "list_customers": "分页会员，含 summaryView 原始 HTML 可进一步清洗",
        "find_customer": "按卡号查，JSON 原生，实用",
        "get_customer_extras": "4 合 1 原始响应，体积大，建议拆分或精简",
        "list_stock": "库存列表，结构化，实用",
        "business_summary": "日营业额首选，metrics 已清洗（含充值实收子指标）",
        "recharge_summary": "时段会员充值汇总，总充值金额/总赠送金额",
        "product_sale_summary": "商品销售汇总+明细，summary 已清洗",
        "list_tickets": "部分门店恒为 0，有 hint 提示",
        "list_stock_flows": "货流单，结构化",
        "list_eshop_orders": "网单，结构化",
        "list_product_purchases": "采购单，结构化",
        "list_suppliers": "供应商下拉，轻量 JSON",
        "stock_change_history": "单商品库存流水，原始 JSON",
    }
    for r in results:
        note = notes.get(r["name"], "")
        if note:
            mark = "✅" if r["ok"] else "❌"
            print(f"  {mark} {r['name']}: {note}")

    # 输出 JSON 供进一步分析
    out_path = "scripts/test_interfaces_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n详细结果已写入 {out_path}")

    client.close()
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
