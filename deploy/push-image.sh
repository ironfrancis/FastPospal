#!/usr/bin/env bash
# 本机构建 linux/amd64 镜像并推到服务器（避免生产机拉基础镜像过慢）
# 日常发布可走 GitHub Actions：push/merge 到 main 自动部署（见 .github/workflows/deploy.yml）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${IMAGE:-fastpospal:latest}"
REMOTE_DIR="${REMOTE_DIR:-/opt/FastPospal}"

if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

SERVER="${SERVER:-}"
if [[ -z "${SERVER}" && -n "${DEPLOY_HOST:-}" ]]; then
  SERVER="${DEPLOY_USER:-root}@${DEPLOY_HOST}"
fi

if [[ -z "${SERVER}" ]]; then
  echo "请设置 SERVER，或在 .env 中配置 DEPLOY_HOST（及可选 DEPLOY_USER）" >&2
  exit 1
fi

echo "==> 构建 ${IMAGE} (linux/amd64) ..."
docker build --platform linux/amd64 -f "${ROOT}/deploy/Dockerfile" -t "${IMAGE}" "${ROOT}"

echo "==> 导出并上传镜像到 ${SERVER} ..."
docker save "${IMAGE}" | gzip -1 | ssh "${SERVER}" 'gunzip | docker load'

echo "==> 同步部署文件（不含 .env / .venv）..."
tar czf - \
  --exclude='.env' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='._*' \
  -C "${ROOT}" . \
  | ssh "${SERVER}" "mkdir -p ${REMOTE_DIR} && tar xzf - -C ${REMOTE_DIR}"

echo "==> 完成。在服务器执行："
echo "    cd ${REMOTE_DIR} && docker compose -f deploy/docker-compose.prod.yml up -d"
