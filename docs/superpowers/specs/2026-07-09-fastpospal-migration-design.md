# FastPospal 迁移与 mmsd Pospal 减负设计

**日期**: 2026-07-09  
**状态**: 已批准（待实施计划）  
**范围**: FastPospal 双层架构、mmsd 内嵌 MCP 下线、pospal-extend 弃用

> 工作区副本：`mmsd-system/docs/superpowers/specs/2026-07-09-fastpospal-migration-design.md`

---

## 1. 背景与目标

萌萌书店此前有两套银豹集成：

- **mmsdv06**：内嵌 MCP（`/mcp/pospal`）、`packages/pospal`、`pospal_api` REST、小萌同学语义工具
- **pospal-extend**：脚本、Notebook、同源 pospal 包

两套使用频率较低。现重建 **FastPospal** 作为面向多场景 Agent 的公共抽象，同时：

- **保留** mmsd Admin 收银页面与 `/pospal-api` REST
- **移除** mmsd 内嵌 MCP 与小萌同学银豹工具（第一期暂不接 FastPospal）
- **弃用** pospal-extend（迁移有价值部分后删除仓库）

---

## 2. 决策记录

| # | 决策点 | 结论 |
|---|--------|------|
| D1 | 切分边界 | 删 mmsd 内嵌 MCP；保留 Admin REST + `packages/pospal` |
| D2 | Admin 页面 | 不动，继续走 `/pospal-api` |
| D3 | 小萌同学 | 同期下线银豹工具；暂不接 FastPospal MCP（可接受暂时无银豹能力） |
| D4 | 客户端维护 | 接受双份：`packages/pospal`（mmsd）与 FastPospal SDK 分开维护 |
| D5 | 备份 | mmsd 打 git tag；pospal-extend 用完即删（本地 + 远程仓库） |
| D6 | MCP 暴露 | 原始层与语义层均暴露；**现有工具名不改** |
| — | FastPospal REST | 暂不做完整 REST；Agent 走 MCP |
| — | 语义层 MCP 命名 | 新增工具使用 `pospal_sem_*` 词缀 |

---

## 3. 目标架构

```
                    ┌──────────────────────────┐
                    │       FastPospal         │
                    │   raw/ + semantic/       │
                    │   MCP (HTTP)             │
                    │ mmsd.site/pospal/mcp     │
                    └────────────┬─────────────┘
                                 │ MCP
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
         OPC Feed            Cursor            未来其他 Agent
         pospal_*            pospal_*          pospal_* + pospal_sem_*

┌────────────────────────────────────────────────────────────┐
│                        mmsdv06                             │
│  Admin 页面 ──→ /pospal-api REST ──→ packages/pospal       │
│  小萌同学 ──→ Chat（第一期无银豹工具）                        │
│  ❌ app/mcp/pospal/                                        │
│  ❌ semantic_tools 银豹部分                                 │
└────────────────────────────────────────────────────────────┘

pospal-extend ──→ 迁移 P0/P1 到 FastPospal ──→ 删仓库
```

---

## 4. FastPospal 双层架构

### 4.1 分层模型

```
MCP Server (server.py)
    │
    ├── pospal_*        原始层工具（现有，命名不变）
    └── pospal_sem_*    语义层工具（新增）

fastpospal/semantic/  ──→  fastpospal/raw/  ──→  client + parsers
```

| | 原始层 `raw/` | 语义层 `semantic/` |
|---|---------------|-------------------|
| 定位 | 银豹 Web API 1:1 映射 | Agent/业务友好高级接口 |
| 来源 | 现有 FastPospal service | mmsd `online.py` + `semantic_tools` |
| MCP 命名 | `pospal_*`（保持不变） | `pospal_sem_*`（新增） |
| 示例 | `pospal_list_products` | `pospal_sem_find_products` |
| 多店 | `user_id` 参数 | `shop_names="关天培店"` 自动解析 |
| 依赖 | 仅 client/parsers | 仅依赖 raw，不直连 HTTP |

### 4.2 建议目录结构

```
fastpospal/
├── raw/
│   ├── client.py
│   ├── parsers.py
│   ├── builders.py
│   └── service.py
├── semantic/
│   ├── categories.py
│   ├── products.py
│   ├── sales.py
│   ├── stock.py
│   └── formatters.py
├── openapi.py
└── __init__.py
```

### 4.3 语义层迁入清单（P0）

| 语义 MCP 工具 | SDK 模块 | mmsd 来源 |
|--------------|----------|-----------|
| `pospal_sem_find_products` | `semantic/products.py` | `find_products` |
| `pospal_sem_check_product_stock` | `semantic/products.py` | `check_product_stock` |
| `pospal_sem_list_products_admin` | `semantic/products.py` | `list_products_admin` |
| `pospal_sem_query_category_sales` | `semantic/sales.py` | `query_category_sales` |
| `pospal_sem_get_store_sales_summary` | `semantic/sales.py` | `get_store_sales_summary` |
| `pospal_sem_query_sales_detail` | `semantic/sales.py` | `query_sales_detail` |
| `pospal_sem_query_stock_flows` | `semantic/stock.py` | `query_stock_flows` |
| `pospal_sem_analyze_restock_needs` | `semantic/stock.py` | `analyze_restock_needs` |

### 4.4 其他迁入优先级

| 优先级 | 来源 | 内容 |
|--------|------|------|
| P0 | mmsd `data_sources/online.py` | 多店、分类消歧、compact 格式 |
| P1 | mmsd `live_queries.py` | HTML 解析边界、分页 |
| P1 | `PospalApisForMCP.json` | 接口清单 |
| P2 | pospal-extend `check_funcs.py` | attribute9 解析（可选） |
| — | pospal-extend 当当/京东工具 | 不迁入（萌萌书店特有） |

---

## 5. mmsd 与 FastPospal 职责对照

| 组件 | 归属 | 状态 |
|------|------|------|
| FastPospal SDK raw | FastPospal | 已有，重构目录 |
| FastPospal SDK semantic | FastPospal | 从 mmsd 迁入 |
| FastPospal MCP | FastPospal | 已部署，扩展语义工具 |
| mmsd `packages/pospal` | mmsd | **保留**（Admin REST） |
| mmsd `pospal_api` REST | mmsd | **保留** |
| mmsd `app/mcp/pospal` | mmsd | **删除** |
| mmsd `semantic_tools` 银豹部分 | mmsd | **下线** |
| pospal-extend | — | **迁移后删除** |

---

## 6. 实施阶段

### Phase 0 — 备份

```bash
cd mmsdv06
git tag backup/pospal-mcp-before-removal
git push origin backup/pospal-mcp-before-removal
```

### Phase 1 — FastPospal 分层重构

1. 现有 `client.py` / `parsers.py` / `builders.py` / `service.py` 迁入 `fastpospal/raw/`
2. 从 mmsd 迁入语义逻辑到 `fastpospal/semantic/`
3. `server.py`：保留现有 `pospal_*`；新增 `pospal_sem_*`
4. 补测试与 `acceptance_test.py`
5. 部署生产，验证 `https://mmsd.site/pospal/mcp`

**注意**：现有 `pospal_*` MCP 工具名**不重命名**，外部消费者（OPC/Cursor）无需改动。

### Phase 2 — 外部 Agent 切换

- OPC Feed / Cursor 改连 `https://mmsd.site/pospal/mcp`
- 确认 Bearer 鉴权（`MCP_AUTH_TOKEN`）
- 语义工具就绪后验收 `pospal_sem_*`

### Phase 3 — mmsd 清理

**删除：**

- `backend/app/mcp/pospal/`（整目录）

**修改：**

- `app/main.py`：移除 MCP 挂载与 lifespan
- `app/core/config.py`：移除 `POSPAL_MCP_*`
- `.env.example`：移除 MCP 相关 env
- `semantic_tools.py`：移除 8 个银豹工具
- `unified_tools.py`、`agent_tools.py`、前端 agent-tools 页面
- 相关测试文件

**保留：**

- `packages/pospal/`、`app/api/v1/pospal_api/`
- `data_sources/online.py`（Admin REST 仍用）
- 前端 `admin/pospal*` 页面
- `POSPAL_USERNAME` / `POSPAL_PASSWORD`

### Phase 4 — pospal-extend 清理

1. 确认 P0/P1 已迁入 FastPospal
2. 本地删除 `pospal-extend/`
3. 删除远程仓库
4. 从 monorepo 工作区移除引用

### Phase 5 — [未来] 小萌同学接回

- mmsd Chat 接入 MCP Client → FastPospal
- 映射 `pospal_sem_*` 为 LangChain 工具
- 恢复 Admin 工具开关

---

## 7. 错误处理

| 层 | 策略 |
|----|------|
| raw | 忠实返回银豹错误；`successed: false` → `RuntimeError` |
| semantic | 分类消歧返回 `category_candidates`；日期超范围自动裁剪；compact 格式 |
| MCP | 写操作在 docstring 标明；session 过期自动 re-login |

---

## 8. 测试策略

| 范围 | 方式 |
|------|------|
| FastPospal raw | `test_interfaces.py` + 单元测试 |
| FastPospal semantic | 从 mmsd `test_sales_tools_behavior.py` 移植 |
| mmsd 清理后 | Admin REST 冒烟保留；MCP 测试删除 |
| 切流验收 | OPC/Cursor 各跑一条 `pospal_*` + `pospal_sem_*` |

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 小萌暂时无银豹能力 | 已接受；Admin 不受影响 |
| 双份 `packages/pospal` 漂移 | 短期接受；长期可改 mmsd 依赖 FastPospal pip |
| pospal-extend 删前遗漏 | Phase 1 完成 P0 后再删 |
| 语义工具与 raw 行为不一致 | semantic 层单测 + 对照 mmsd 历史用例 |

---

## 10. 不在范围内

- FastPospal 完整 REST API（Admin 继续用 mmsd `/pospal-api`）
- pospal-extend 当当/京东/Notebook 迁入
- 小萌同学第一期接 FastPospal MCP
- mmsd `packages/pospal` 合并入 FastPospal SDK
