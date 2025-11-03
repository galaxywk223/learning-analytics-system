#!/usr/bin/env bash

set -Eeuo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "缺少命令: $1"
    exit 1
  }
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
FRONTEND_DIR="${REPO_ROOT}/frontend"
VENV_DIR="${BACKEND_DIR}/venv"
UPLOAD_TARGET="${UPLOAD_TARGET:-/srv/learning-analytics/uploads}"
SYSTEMD_UNIT="${SYSTEMD_UNIT:-learning-analytics.service}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.12}"

require_cmd "${PYTHON_BIN}"
require_cmd npm
require_cmd systemctl

if [ ! -d "${UPLOAD_TARGET}" ]; then
  log "创建上传目录: ${UPLOAD_TARGET}"
  mkdir -p "${UPLOAD_TARGET}"
fi

if [ ! -L "${BACKEND_DIR}/uploads" ]; then
  if [ -e "${BACKEND_DIR}/uploads" ]; then
    log "移除已有 uploads 目录以创建符号链接"
    rm -rf "${BACKEND_DIR}/uploads"
  fi
  ln -s "${UPLOAD_TARGET}" "${BACKEND_DIR}/uploads"
  log "已建立 uploads 符号链接 -> ${UPLOAD_TARGET}"
fi

if [ ! -d "${VENV_DIR}" ]; then
  log "初始化 Python 虚拟环境: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

log "升级 pip & 安装后端依赖"
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt"

log "执行数据库迁移 (若失败需手动处理)"
pushd "${BACKEND_DIR}" >/dev/null
if ! FLASK_APP=run.py FLASK_ENV=production "${VENV_DIR}/bin/flask" db upgrade; then
  log "!!! 数据库迁移失败，请手动检查"
fi
popd >/dev/null

log "安装前端依赖并构建"
pushd "${FRONTEND_DIR}" >/dev/null
npm install
npm run build
popd >/dev/null

log "重启服务 ${SYSTEMD_UNIT}"
systemctl restart "${SYSTEMD_UNIT}"
systemctl status "${SYSTEMD_UNIT}" --no-pager

log "部署脚本执行完成"
