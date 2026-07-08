# FastPospal

银豹 PosPal 逆向 MCP 服务 — 基于云后台私有 Web API 流量逆向，为 AI Agent 提供商品、会员、库存、货流、单据等 **读 + 写** 工具集。

> 开发验证时使用弃用测试门店；开源文档不含真实门店/会员信息。  
> 最后更新：2026-07-09

---

## 快速开始

本项目使用 **[uv](https://docs.astral.sh/uv/)** 管理 Python 环境与依赖（比 `pip + venv` 更快，且有 `uv.lock` 锁定版本）。

### 0. 安装 uv（若尚未安装）

```bash
# macOS
brew install uv

# 或官方脚本
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. 安装依赖

```bash
cd FastPospal
uv sync          # 创建 .venv + 按 uv.lock 安装依赖
```

> 等价于以前的 `python -m venv .venv && pip install -e .`，但更快、可复现。

### 2. 配置账号

```bash
cp .env.example .env
# 编辑 .env
```

```env
POSPAL_ACCOUNT=your_account
POSPAL_PASSWORD=your_password
```

### 3. 启动 MCP

**STDIO（Cursor / Claude Desktop 推荐）：**

```bash
uv run fastmcp run server.py:mcp
```

**HTTP（远程 / 调试）：**

```bash
uv run fastmcp run server.py:mcp --transport http --port 8000
```

**加载 `.env` 中的账号（本地调试）：**

```bash
uv run --env-file .env fastmcp run server.py:mcp
```

### 4. 接入 Cursor

`~/.cursor/mcp.json` 或项目 MCP 设置。**推荐用 `uv run`**，无需写 `.venv/bin/fastmcp` 绝对路径：

```json
{
  "mcpServers": {
    "fastpospal": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/FastPospal",
        "run", "fastmcp", "run", "server.py:mcp"
      ],
      "env": {
        "POSPAL_ACCOUNT": "your_account",
        "POSPAL_PASSWORD": "your_password"
      }
    }
  }
}
```

> Cursor 不会自动读 `.env`，账号密码需写在上面 `env` 里，或使用 `--env-file`（需 uv 0.4+）：
>
> ```json
> "args": ["--directory", "/path/to/FastPospal", "run", "--env-file", ".env", "fastmcp", "run", "server.py:mcp"]
> ```

重启 Cursor 后，在 Agent 对话中即可调用 `pospal_*` 工具。

---

## 远程部署（服务器 HTTP MCP）

本地 stdio 适合个人开发；**多人 / 多设备共用**时，把 MCP 部署到服务器，Cursor 通过 URL 连接。

### 架构

```
Cursor (本机)  ──HTTPS──▶  Nginx (443)  ──▶  uvicorn (8000)  ──▶  FastPospal MCP
                              │                      │
                         TLS 证书              银豹账号在服务器 .env
                         Bearer 鉴权            客户端无需 POSPAL 密码
```

MCP 端点：`https://your-domain.com/mcp/`（**注意末尾斜杠**）

### 1. 服务器上安装并配置

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 拉代码
git clone <your-repo> /opt/FastPospal
cd /opt/FastPospal
uv sync

# 配置环境变量
cp .env.example .env
vim .env
```

`.env` 至少包含：

```env
POSPAL_ACCOUNT=银豹账号
POSPAL_PASSWORD=银豹密码
MCP_AUTH_TOKEN=请换成随机长字符串
FASTMCP_STATELESS_HTTP=true
```

> **安全**：银豹账号只放在服务器 `.env`；客户端用 `MCP_AUTH_TOKEN` 鉴权，不要暴露银豹密码。

### 2. 启动 HTTP 服务

**开发 / 内网测试**（绑定所有网卡）：

```bash
MCP_HOST=0.0.0.0 MCP_PORT=8000 uv run fastmcp run server.py:mcp --transport http --host 0.0.0.0 --port 8000
```

**生产推荐**（ASGI + uvicorn）：

```bash
uv run uvicorn app:app --host 127.0.0.1 --port 8000
```

`app.py` 已导出 `app = mcp.http_app()`，并支持可选 `MCP_AUTH_TOKEN` Bearer 鉴权。

### 3. Docker 部署

**标准模式**（映射宿主机 8000 端口，适合单机或内网）：

```bash
cd /opt/FastPospal
# 确保 .env 在项目根目录
docker compose -f deploy/docker-compose.yml up -d --build
```

服务监听 `http://0.0.0.0:8000/mcp/`。

**生产模式**（接入已有 Docker 网络，不映射端口；Nginx 同网反代）：

```bash
# 推荐：本机构镜像再推送（服务器不 build，避免拉基础镜像慢）
./deploy/push-image.sh

# 服务器上（.env 含银豹账号 + MCP_AUTH_TOKEN）
cd /opt/FastPospal
docker compose -f deploy/docker-compose.prod.yml up -d
```

`push-image.sh` 会：本机 `docker build --platform linux/amd64` → `docker save | gzip | ssh docker load` → 同步 compose / nginx 片段到 `/opt/FastPospal`。

**萌萌书店生产示例**：

| 场景 | URL |
|------|-----|
| 公网（Cursor / 外网） | `https://mmsd.site/pospal/mcp/` |
| Docker 内网（网站 AI） | `http://fastpospal:8000/mcp/` |

Nginx 片段见 `deploy/nginx-mmsd-pospal-mcp.conf`，追加到 `mmsdv06-https.conf` 的 `location /` 之前。

> `deploy/docker-compose.prod.yml` 使用预加载镜像 `fastpospal:latest`（`pull_policy: never`），不在服务器上 build。

### 4. systemd 常驻（裸机）

```bash
sudo cp deploy/fastpospal.service /etc/systemd/system/
# 编辑 WorkingDirectory / User / uv 路径
sudo systemctl enable --now fastpospal
```

### 5. Nginx + HTTPS（公网必做）

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/fastpospal
# 修改域名与证书路径
sudo ln -s /etc/nginx/sites-available/fastpospal /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

关键配置：`proxy_buffering off;`、`proxy_read_timeout 300s;`（Streamable HTTP 需要）

### 6. Cursor 连接远程 MCP

`~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "fastpospal-remote": {
      "url": "https://your-domain.com/mcp/",
      "headers": {
        "Authorization": "Bearer 你的MCP_AUTH_TOKEN"
      }
    }
  }
}
```

保存并重启 Cursor，MCP 面板显示绿色即连接成功。

### 7. 验证远程服务

```bash
# 健康：应返回 MCP 协议响应或 401（若开了鉴权）
curl -i https://your-domain.com/mcp/

# 带 Token 测试（需 MCP 客户端；或本机 Python）
uv run python -c "
import asyncio
from fastmcp import Client

async def main():
    async with Client(
        'https://your-domain.com/mcp/',
        headers={'Authorization': 'Bearer 你的MCP_AUTH_TOKEN'},
    ) as c:
        r = await c.call_tool('pospal_session_info', {})
        print(r)

asyncio.run(main())
"
```

### 部署清单

| 项 | 说明 |
|----|------|
| HTTPS | 公网必须，避免 Token / 数据明文传输 |
| `MCP_AUTH_TOKEN` | 必设，否则任何人可调用写接口改门店数据 |
| 防火墙 | 仅开放 443；8000 只绑 `127.0.0.1` 或内网 |
| `FASTMCP_STATELESS_HTTP=true` | 多 worker / 负载均衡时必须 |
| 日志 | 不要打印 POSPAL_PASSWORD |

### 本地 vs 远程对比

| | 本地 stdio | 远程 HTTP |
|---|-----------|-----------|
| Cursor 配置 | `command: uv` | `url: https://.../mcp/` |
| 银豹账号 | 本机 env | 服务器 `.env` |
| 适用 | 个人开发 | 团队 / 多设备 / 7×24 |
| 安全 | 本机隔离 | 必须 HTTPS + Token |

### 备选：不用 uv 时

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -e .
fastmcp run server.py:mcp
```

---

## 如何使用（Agent 对话示例）

在 Cursor Agent 里直接用自然语言，模型会自动选用 MCP 工具：

| 你说的话 | 调用的工具 |
|----------|-----------|
| 「查一下店里有多少商品」 | `pospal_product_summary` |
| 「搜索条码 6901234567890 的商品」 | `pospal_find_product_by_barcode` |
| 「列出前 10 个会员」 | `pospal_list_customers` |
| 「查会员 13800138000 的详情」 | `pospal_find_customer` |
| 「查 7 月份的销售单据」 | `pospal_list_tickets` |
| 「查全店库存，关键词 晨光」 | `pospal_list_stock` |
| 「创建一个测试商品叫 MCP测试品」 | `pospal_create_product` |
| 「删除 productId 为 123 的商品」 | `pospal_delete_product` |

**时间格式统一为：** `YYYY-MM-DD HH:MM:SS`，例如 `2026-07-01 00:00:00`。

**Python 脚本直接调用（不经过 MCP）：**

```bash
uv run python your_script.py
```

```python
from dotenv import load_dotenv
load_dotenv()

from fastpospal.client import PospalClient
from fastpospal.service import PospalService
import os

client = PospalClient(os.environ["POSPAL_ACCOUNT"], os.environ["POSPAL_PASSWORD"])
client.login()
svc = PospalService(client)

print(svc.product_summary())                          # 商品总数
print(svc.find_product_by_barcode("6901234567890"))    # 条码查商品
print(svc.list_customers(page_size=5))                # 会员列表
client.close()
```

---

## MCP 能力清单

图例：**✅ 已验证** · **⚠️ 部分限制** · **🔧 写操作**

### 会话

| 工具 | 类型 | 状态 | 说明 |
|------|------|------|------|
| `pospal_session_info` | 读 | ✅ | 门店子域、userId、会话是否有效 |
| `pospal_login` | 写 | ✅ | 强制重新登录，刷新 cookie |

### 分类

| 工具 | 银豹 API | 类型 | 状态 |
|------|----------|------|------|
| `pospal_list_categories` | `/Category/LoadCategoryDDLJson` | 读 | ✅ |
| `pospal_create_category` 🔧 | `/Category/AddNewCategory` | 写 | ✅ |
| `pospal_update_category` 🔧 | `/Category/Update` | 写 | ✅ |
| `pospal_delete_categories` 🔧 | `/Category/Delete` | 写 | ✅ |

### 商品

| 工具 | 银豹 API | 类型 | 状态 |
|------|----------|------|------|
| `pospal_product_summary` | `/Product/LoadProductSummary` | 读 | ✅ |
| `pospal_list_products` | `/Product/LoadProductsByPage` | 读 | ✅ HTML→JSON |
| `pospal_get_product` | `/Product/FindProduct` | 读 | ✅ |
| `pospal_find_product_by_barcode` | 组合查询 | 读 | ✅ |
| `pospal_create_product` 🔧 | `/Product/SaveProduct` | 写 | ✅ 已实测 CRUD |
| `pospal_update_product` 🔧 | `/Product/SaveProduct` | 写 | ✅ |
| `pospal_delete_product` 🔧 | `/Product/DeleteProduct` | 写 | ✅ |

> **注意：** `SaveProduct.stock` 对已有商品**不会**改实际库存；真实库存变更需走货流模块（`/StockFlow/CreateStockFlowIn` 等，尚未完全封装）。

### 会员

| 工具 | 银豹 API | 类型 | 状态 |
|------|----------|------|------|
| `pospal_find_customer` | `/Customer/FindCustomer` | 读 | ✅ |
| `pospal_list_customers` | `/Customer/LoadCustomersByPage` | 读 | ✅ 需 `type=1` |
| `pospal_get_customer_extras` | 次卡/权益卡/购物卡/优惠券 | 读 | ✅ |
| `pospal_create_customer` 🔧 | `/Customer/SaveCustomer` | 写 | ✅ |
| `pospal_update_customer` 🔧 | `/Customer/SaveCustomer` | 写 | ✅ 备注等 |
| `pospal_delete_customer` 🔧 | `/Customer/DeleteCustomer` | 写 | ✅ 软删除 |

> **注意：** 余额/积分修改需门店开启「会员积分余额编辑」（`editMoneyPoint=True`）；本测试店为 `False`，SaveCustomer 成功但 money/point 不变。

### 库存 / 货流

| 工具 | 银豹 API | 类型 | 状态 |
|------|----------|------|------|
| `pospal_list_stock` | `/Inventory/LoadStockCountByPage` | 读 | ✅ |
| `pospal_stock_change_history` | `/Inventory/LoadStockChangeHistory` | 读 | ✅ |
| `pospal_list_stock_flows` | `/StockFlow/LoadStockFlowByPage` | 读 | ✅ |
| `pospal_set_product_stock_limit` 🔧 | `/Product/SaveProductStockLimit` | 写 | ✅ 上下限，非实际库存 |

### 供应商 / 单据 / 网单 / 采购

| 工具 | 银豹 API | 类型 | 状态 |
|------|----------|------|------|
| `pospal_list_suppliers` | `/Supplier/LoadSupplierDDLJson` | 读 | ✅ |
| `pospal_list_tickets` | `/Report/LoadTicketsByPage` | 读 | ✅ 本店近期无单据 |
| `pospal_list_eshop_orders` | `/EshopOrder/LoadOrdersByPage` | 读 | ✅ |
| `pospal_list_product_purchases` | `/ProductPurchase/LoadProductPurchaseByPage` | 读 | ✅ |

### 官方开放平台（可选）

| 工具 | 说明 |
|------|------|
| `pospal_openapi_status` | 检查 `POSPAL_APP_ID` / `POSPAL_APP_KEY` 是否配置 |

---

## 逆向 API 参考

### 认证流程

```
POST https://beta.pospal.cn/account/SignIn
  → 返回 { successed, msg: "https://betaXX.pospal.cn/Home?..." }
  → Set-Cookie: .POSPALAUTH* (domain=.pospal.cn)
  → 后续请求发往门店子域（登录响应 msg 中的域名）
```

### 通用请求格式

- **Method:** POST
- **Content-Type:** `application/x-www-form-urlencoded; charset=UTF-8`
- **Header:** `X-Requested-With: XMLHttpRequest`
- JSON 数据嵌在 form 字段中（如 `productJson=...`、`customerJson=...`）

### 已知限制

| 限制 | 说明 |
|------|------|
| 列表接口返回 HTML | 服务端用 BeautifulSoup 解析为 JSON |
| 单据无 Web 作废 API | 作废在 POS 端操作；后台用 `reversed=1` 筛选 |
| 单据无独立详情 API | 明细内嵌于 `LoadTicketsByPage` HTML |
| uid 为 bigInt | JS/Python 注意精度，建议用字符串 |
| 货流入库 | `CreateStockFlowIn` 需完整 `stockOrderJson`，待进一步封装 |
| 供应商 SaveSupplier | 本账号持续 500，读接口正常 |

---

## 项目结构

```
FastPospal/
├── server.py              # FastMCP 入口（30+ 工具）
├── fastpospal/
│   ├── client.py          # 登录、会话、AJAX 封装
│   ├── service.py         # 业务 API（读 + 写）
│   ├── parsers.py         # HTML 表格 → JSON
│   ├── builders.py        # SaveProduct/SaveCustomer 载荷构造
│   └── openapi.py         # 官方开放平台（可选）
├── .env.example
└── pyproject.toml
```

---

## 安全说明

- **切勿**将 `.env`、`.pospal_session.json` 提交到 Git
- 标记 🔧 的写工具会修改门店真实数据
- 仅用于自有/弃用测试账号的技术研究与自动化集成
- 生产环境建议申请[银豹官方开放平台](https://pospal.cn/openplatform/index.html)凭证

---

## 更新日志

### 2026-07-09 (c)

- 新增远程 HTTP 部署：`app.py`（ASGI）、Docker、systemd、Nginx 示例
- 支持 `MCP_AUTH_TOKEN` Bearer 鉴权、`MCP_HOST`/`MCP_PORT` 环境变量

### 2026-07-09 (b)

- 改用 **uv** 管理依赖（`uv sync` / `uv run`），生成 `uv.lock`
- Cursor MCP 推荐配置：`command: uv` + `--directory` + `run fastmcp ...`

### 2026-07-09

- 4 路并行 Agent 嗅探：商品、会员、库存货流、单据分类供应商
- 新增 **18 个写工具**（商品/分类/会员 CRUD、库存上下限）
- 新增库存、货流、供应商、网单、采购读工具
- 修复会员列表 `type=""` 导致 500 的问题
- 验证商品完整 CRUD、分类 CRUD、会员 CRUD

### 2026-07-08

- 初始版本：登录 + 商品/会员/单据读工具

---

## License

MIT
