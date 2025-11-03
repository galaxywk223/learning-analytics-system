#!/usr/bin/env bash

set -Eeuo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "missing command: $1"
    exit 1
  fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
FRONTEND_DIR="${REPO_ROOT}/frontend"
VENV_DIR="${BACKEND_DIR}/venv"
UPLOAD_TARGET="${UPLOAD_TARGET:-/srv/learning-analytics/uploads}"
SYSTEMD_UNIT="${SYSTEMD_UNIT:-learning-analytics.service}"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.12}"

if [ ! -x "${PYTHON_BIN}" ]; then
  log "python interpreter not executable: ${PYTHON_BIN}"
  exit 1
fi
require_cmd npm
require_cmd systemctl

ENV_FILE="${BACKEND_DIR}/.env"

if [ ! -d "${UPLOAD_TARGET}" ]; then
  log "creating uploads directory at ${UPLOAD_TARGET}"
  mkdir -p "${UPLOAD_TARGET}"
fi

if [ ! -L "${BACKEND_DIR}/uploads" ]; then
  if [ -e "${BACKEND_DIR}/uploads" ]; then
    log "removing existing uploads path to create symlink"
    rm -rf "${BACKEND_DIR}/uploads"
  fi
  ln -s "${UPLOAD_TARGET}" "${BACKEND_DIR}/uploads"
  log "uploads symlink created -> ${UPLOAD_TARGET}"
fi

if [ ! -d "${VENV_DIR}" ]; then
  log "initialising python virtualenv at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

log "installing backend dependencies"
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt"

log "running database migrations (ignored if they fail)"
if [ -f "${ENV_FILE}" ]; then
  log "loading environment from ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi
pushd "${BACKEND_DIR}" >/dev/null
if ! FLASK_APP=run.py FLASK_ENV=production "${VENV_DIR}/bin/flask" db upgrade; then
  log "WARNING: flask db upgrade failed, please check manually"
fi
popd >/dev/null

log "installing frontend dependencies and building"
pushd "${FRONTEND_DIR}" >/dev/null
npm install
npm run build
popd >/dev/null

log "restarting service ${SYSTEMD_UNIT}"
systemctl restart "${SYSTEMD_UNIT}"
systemctl status "${SYSTEMD_UNIT}" --no-pager

log "deploy script finished"
