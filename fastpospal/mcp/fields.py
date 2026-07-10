"""MCP 工具共享参数类型（供 JSON Schema 生成参数说明）。"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

# ── 分页（raw 层） ────────────────────────────────────────

PageIndex = Annotated[
    int,
    Field(description="页码，从 1 开始", ge=1),
]
PageSize = Annotated[
    int,
    Field(description="每页条数", ge=1, le=100),
]

# ── 分页（semantic 层） ───────────────────────────────────

SemPage = Annotated[
    int,
    Field(description="页码，从 1 开始", ge=1),
]
SemSize = Annotated[
    int,
    Field(description="每页条数", ge=1, le=100),
]

# ── 时间（raw 层，完整 datetime） ─────────────────────────

BeginDatetime = Annotated[
    str,
    Field(
        description="开始时间，格式 YYYY-MM-DD HH:mm:ss，例如 2026-07-08 00:00:00",
        examples=["2026-07-08 00:00:00"],
    ),
]
EndDatetime = Annotated[
    str,
    Field(
        description="结束时间，格式 YYYY-MM-DD HH:mm:ss，例如 2026-07-08 23:59:59",
        examples=["2026-07-08 23:59:59"],
    ),
]
BeginTime = BeginDatetime
EndTime = EndDatetime

# ── 时间（semantic 层，仅日期） ───────────────────────────

StartDate = Annotated[
    str,
    Field(
        description="开始日期 YYYY-MM-DD；留空默认近 7 天起始日",
        examples=["2026-07-01"],
    ),
]
EndDate = Annotated[
    str,
    Field(
        description="结束日期 YYYY-MM-DD；留空默认今天",
        examples=["2026-07-08"],
    ),
]

# ── 门店 / 商品 / 会员 ───────────────────────────────────

ShopNames = Annotated[
    str,
    Field(
        description="门店名称，逗号分隔多店；留空默认关天培店。可用 POSPAL_SHOP_NAME_TO_ID 配置映射",
        examples=["关天培店", "关天培店,山阳湖店"],
    ),
]
ProductKeyword = Annotated[
    str,
    Field(description="商品搜索词：条码、名称或拼音码"),
]
ProductEnable = Annotated[
    str,
    Field(description="商品状态：1=启用（默认）, 0=禁用"),
]
ProductId = Annotated[
    int,
    Field(description="商品数字 ID（productId），来自 list_products 或 get_product"),
]
ProductUid = Annotated[
    str,
    Field(description="商品 UID 字符串（productUid），与 productId 不同，用于库存上下限等接口"),
]
CategoryUid = Annotated[
    str,
    Field(description="分类 UID 字符串（categoryUid），来自 list_categories"),
]
Barcode = Annotated[
    str,
    Field(description="商品条码"),
]
CustomerNumber = Annotated[
    str,
    Field(description="会员卡号或手机号"),
]
CustomerType = Annotated[
    str,
    Field(description="会员筛选：1=启用（默认）, 0=禁用, 2=过期"),
]

# ── 语义层通用 ────────────────────────────────────────────

SemKeyword = Annotated[
    str,
    Field(description="商品名称或条码，支持模糊匹配"),
]
SemSearch = Annotated[
    str,
    Field(description="销售明细筛选词：商品名、条码或分类关键词；留空查全部"),
]
SemLimit = Annotated[
    int,
    Field(description="最多返回条数", ge=1, le=50),
]
SemCompact = Annotated[
    bool,
    Field(description="true 时压缩返回，仅保留关键列，适合 Agent 阅读"),
]
CategoryName = Annotated[
    str,
    Field(description="分类名称关键词，自动匹配分类（无需先查分类列表）"),
]

# ── 报表 ──────────────────────────────────────────────────

OrderSource = Annotated[
    str,
    Field(
        description=(
            "订单渠道：留空=全部；ZIYING=自营、xianxia=线下、"
            "MEITUAN_WAIMAI=美团、ELEME_WAIMAI=饿了么"
        ),
    ),
]
TicketType = Annotated[
    str,
    Field(description="单据类型：0=有效（默认）, 1=作废, 4=退货, 2=会员, 3=批发"),
]
TicketSn = Annotated[
    str,
    Field(description="销售单号精确筛选；留空查全部"),
]
PaymentMethod = Annotated[
    str,
    Field(description="充值支付方式筛选；留空查全部"),
]
