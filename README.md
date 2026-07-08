# FastPospal

> **银豹 PosPal Python SDK 与 MCP Server**

FastPospal 是一个面向 **银豹 PosPal Web 后台** 的 Python SDK 与 MCP
Server，为开发者和 AI Agent
提供商品、会员、库存、货流、单据等业务能力的统一自动化接口。

> **声明**
>
> -   本项目为社区维护项目，与银豹官方不存在任何关联。
> -   请仅在拥有合法授权的账号和门店中使用。
> -   本项目旨在提高自动化集成效率，不提供任何绕过认证或破解系统的能力。
> -   如官方开放平台能够满足业务需求，建议优先使用官方接口。

------------------------------------------------------------------------

## ✨ 特性

-   Python SDK
-   FastMCP Server（STDIO / HTTP）
-   商品、分类、会员 CRUD
-   库存、货流、单据查询
-   Cursor / Claude Desktop 开箱即用
-   uv 管理依赖
-   Docker、systemd、Nginx 部署支持

------------------------------------------------------------------------

## 为什么选择 FastPospal？

银豹官方开放平台覆盖能力有限，而 Web 后台拥有更丰富的业务接口。

FastPospal 对这些能力进行了统一封装：

-   Python 程序可直接调用
-   AI Agent 可通过 MCP 自动调用
-   后续可扩展 CLI、REST API 等能力

MCP 只是接口形式，Python SDK 才是核心能力。

------------------------------------------------------------------------

## 快速开始

### 安装 uv

``` bash
brew install uv
```

### 安装依赖

``` bash
uv sync
```

### 配置账号

``` bash
cp .env.example .env
```

填写：

``` text
POSPAL_ACCOUNT=your_account
POSPAL_PASSWORD=your_password
```

### 启动 MCP

STDIO：

``` bash
uv run fastmcp run server.py:mcp
```

HTTP：

``` bash
uv run fastmcp run server.py:mcp --transport http --port 8000
```

------------------------------------------------------------------------

## Python SDK 示例

``` python
from fastpospal.client import PospalClient
from fastpospal.service import PospalService

client = PospalClient(account, password)
client.login()

svc = PospalService(client)

print(svc.product_summary())
```

------------------------------------------------------------------------

## MCP 使用示例

在 Cursor 或 Claude Desktop 中：

> 查询今天商品总数

> 搜索条码 6901234567890

> 创建一个测试商品

Agent 将自动调用对应 MCP 工具。

------------------------------------------------------------------------

## 远程 HTTP 部署（Nginx + Docker）

适用于 OPC Feed、Cursor 等通过 HTTPS 远程连接 MCP。

1.  配置 `.env`：`POSPAL_*`、`MCP_AUTH_TOKEN`，以及公网域名白名单：

    ``` text
    FASTMCP_HTTP_ALLOWED_HOSTS=["your-domain.com"]
    ```

    经 Nginx 反代时 **必须** 设置，否则 Bearer 鉴权通过后 FastMCP 会因 `Host`
    校验返回 **421 Misdirected Request**。

2.  启动容器：`docker compose -f deploy/docker-compose.prod.yml up -d`

3.  Nginx 反代 **不要用尾斜杠**（`/pospal/mcp` 而非 `/pospal/mcp/`），否则 FastMCP
    会 307 到错误路径。萌萌书店示例见
    `deploy/nginx-mmsd-pospal-mcp.conf`。

4.  客户端 MCP URL 与 Nginx location 保持一致，例如
    `https://mmsd.site/pospal/mcp`。

### GitHub Actions 自动部署

`main` 分支 push 或 merge 后，`.github/workflows/deploy.yml` 会自动：

1.  `uv sync` + 静态检查
2.  构建 `linux/amd64` 镜像
3.  SSH 上传到生产机并 `docker compose up -d`

首次启用需在 GitHub 仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 |
|--------|------|
| `SSH_PRIVATE_KEY` | 能登录生产机的私钥（对应公钥写入服务器 `authorized_keys`） |
| `DEPLOY_HOST` | 生产机 IP 或域名（不含用户名） |
| `DEPLOY_USER` | SSH 登录用户，例如 `root` |

服务器上的 `.env` **不会**被同步覆盖（仅含运行时 `POSPAL_*`、`MCP_AUTH_TOKEN` 等，不含 SSH 部署地址）。

本地紧急发布：在 `.env` 配置 `DEPLOY_HOST` / `DEPLOY_USER` 后执行 `bash deploy/push-image.sh`，或临时 `SERVER=root@your-host bash deploy/push-image.sh`。

------------------------------------------------------------------------

## 架构

``` text
AI Agent
(Cursor / Claude)

        │

        ▼

 FastPospal MCP

        │

 FastPospal SDK

        │

 PosPal Web
```

------------------------------------------------------------------------

## Roadmap

-   [x] 登录与会话管理
-   [x] 商品管理
-   [x] 分类管理
-   [x] 会员管理
-   [x] 库存查询
-   [x] HTTP MCP
-   [ ] CLI
-   [ ] PyPI 发布
-   [ ] 自动化测试
-   [ ] 官方 OpenAPI 适配

------------------------------------------------------------------------

## License

MIT
