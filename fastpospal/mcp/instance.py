from __future__ import annotations

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

MCP_INSTRUCTIONS = """\
银豹 PosPal 门店 MCP 服务。封装银豹云后台 Web API，支持商品/分类/会员/库存/货流/单据/网单/采购的读写。
写操作（标注【写】）会修改门店真实数据，仅在测试账号或明确授权时使用。
环境变量：POSPAL_ACCOUNT, POSPAL_PASSWORD；多门店可选 POSPAL_SHOP_NAME_TO_ID。

## 两层 API 如何选型

- **pospal_sem_***（语义层，推荐）：自然语言查询，接受日期 YYYY-MM-DD、门店名 shop_names，返回 {ok, data} 结构。
- **pospal_***（原始层）：精确 CRUD 与报表字段，时间多为 YYYY-MM-DD HH:mm:ss，适合需要原始字段名时。

## 常见场景 → 推荐工具

| 场景 | 优先工具 | 不要用 |
|------|----------|--------|
| 日营业额 / 客单数 | pospal_business_summary 或 pospal_sem_get_store_sales_summary | pospal_list_tickets（部分门店恒为 0） |
| 时段会员充值总额 | pospal_recharge_summary | pospal_list_customers 的 summary |
| 商品销售汇总 | pospal_product_sale_summary 或 pospal_sem_query_category_sales | — |
| 按名称/条码找商品 | pospal_sem_find_products | — |
| 查单品库存 | pospal_sem_check_product_stock | pospal_list_stock（全店分页） |
| 逐笔销售流水 | pospal_sem_query_sales_detail | pospal_list_tickets |
| 商品 CRUD | pospal_get_product / pospal_create_product 等 | pospal_sem_* |

## 时间参数注意

- raw 报表：begin_datetime / end_datetime 或 begin_time / end_time → YYYY-MM-DD HH:mm:ss
- semantic：start_date / end_date → YYYY-MM-DD，留空默认近 7 天
"""

mcp = FastMCP("FastPospal", instructions=MCP_INSTRUCTIONS)
