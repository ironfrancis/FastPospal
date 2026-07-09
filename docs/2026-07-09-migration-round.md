# 2026-07-09 迁移轮次说明

## 本地启动验证

```bash
cd FastPospal
uv sync
cp .env.example .env   # 填写 POSPAL_ACCOUNT / POSPAL_PASSWORD

# 单元测试
uv run pytest tests/ -q

# SDK 集成验收（需银豹账号）
uv run python scripts/acceptance_test.py

# 启动 MCP HTTP（默认 http://127.0.0.1:8000/mcp）
uv run python server.py
```

Cursor 本地 MCP 配置示例：

```json
{
  "mcpServers": {
    "fastpospal": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 本轮优化摘要

### 1. 架构：原始层 / 语义层分离

- **`fastpospal/raw/`**：银豹 Web API 1:1 映射（client、parsers、builders、service）
- **`fastpospal/semantic/`**：Agent 友好业务接口（多店、分类消歧、补货分析等）
- 顶层 `fastpospal/client.py` 等保留为**向后兼容 shim**，旧 import 路径仍可用

### 2. MCP 工具命名策略

| 层级 | 命名 | 说明 |
|------|------|------|
| 原始层 | `pospal_*` | **现有工具不改名**，OPC/Cursor 无需改配置 |
| 语义层 | `pospal_sem_*` | 新增 8 个工具，从 mmsd 语义层迁入 |

新增语义工具：`find_products`、`check_product_stock`、`query_category_sales`、`get_store_sales_summary`、`query_sales_detail`、`query_stock_flows`、`list_products_admin`、`analyze_restock_needs`。

### 3. 从 mmsd 迁入的能力

- 多店 `shop_names` → `POSPAL_SHOP_NAME_TO_ID`（可 env 覆盖）
- 分类 DDL 压平与关键词消歧（`category_candidates`）
- ReportV2 `LoadProductSaleByPage` 原始接口封装
- 补货分析逻辑（`analyze_restock_needs`）
- compact 响应格式（`headers` + `data`）

### 4. mmsd 减负

- 删除内嵌 `app/mcp/pospal/` 与 `POSPAL_MCP_*` 配置
- 小萌同学银豹语义工具下线（`semantic_tools` 返回空列表）
- **保留** Admin `/pospal-api` REST 与 `packages/pospal`
- git tag：`backup/pospal-mcp-before-removal`

### 5. Bug 修复（验证中发现）

- **Session Cookie 冲突**：银豹登录后 httpx 存在同名 `sessionGuid` cookie，`dict(cookies)` 会抛 `CookieConflict`；改为按 jar 序列化完整 cookie 列表（含 domain/path）

## 本地验证结果（2026-07-09）

| 项目 | 结果 |
|------|------|
| `pytest tests/` | 17 passed |
| `scripts/acceptance_test.py` | PASS=22 FAIL=0 |
| 语义层冒烟 | `get_store_sales_summary`、`analyze_restock_needs` 正常 |
| MCP HTTP | `uv run python server.py` → `http://127.0.0.1:8000/mcp` 启动成功 |

## 后续

- [ ] push FastPospal / mmsdv06 到远程并部署生产
- [ ] OPC/Cursor 切到 `https://mmsd.site/pospal/mcp`
- [ ] 删除 `pospal-extend` 仓库
- [ ] Phase 5：小萌同学通过 MCP Client 接回 `pospal_sem_*`
