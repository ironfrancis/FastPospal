# 贡献指南

感谢你对 FastPospal 的关注！本项目是社区维护的银豹 PosPal Python SDK 与 MCP Server，欢迎提交 Issue 与 Pull Request。

## 开始之前

- 请仅在**拥有合法授权**的银豹账号与门店中使用、测试本项目。
- 本项目与银豹官方无关联；若官方开放平台已满足需求，建议优先使用官方接口。
- 请勿提交包含真实账号、密码、Token、会话文件或门店私有数据的 PR。

## 开发环境

**要求：** Python 3.11+，[uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/ironfrancis/FastPospal.git
cd FastPospal
uv sync
cp .env.example .env   # 填入测试账号（勿提交）
```

## 运行测试

解析器相关测试为离线 fixture，不依赖网络：

```bash
uv run pytest
```

静态检查：

```bash
uv run python -m compileall fastpospal server.py app.py
```

## 提交 Pull Request

1. 从 `main` 创建分支，命名建议：`fix/xxx`、`feat/xxx`、`docs/xxx`
2. 保持改动聚焦，遵循现有代码风格与目录结构
3. 若修改解析逻辑或 SDK 行为，请补充或更新 `tests/` 中的用例
4. 在 PR 描述中说明：变更动机、影响范围、如何验证
5. 确保本地 `pytest` 与 `compileall` 通过

## Issue 规范

提交 Issue 前请先搜索是否已有重复讨论。推荐使用仓库提供的 Issue 模板：

- **Bug 报告**：复现步骤、期望与实际行为、环境信息
- **功能建议**：使用场景、期望 API / MCP 工具形态、是否愿意自行实现

## 代码范围说明

| 目录 | 说明 |
|------|------|
| `fastpospal/` | Python SDK 核心 |
| `server.py` | MCP Server 工具定义 |
| `app.py` | HTTP ASGI 入口 |
| `tests/` | 单元测试 |
| `deploy/` | Docker / Nginx 部署示例 |
| `scripts/` | 本地验收脚本（可选） |

## 获取帮助

如有疑问，可开 Issue 并打上 `question` 标签。
