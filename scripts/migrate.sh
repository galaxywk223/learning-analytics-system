#!/usr/bin/env bash

set -Eeuo pipefail

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
VENV_DIR="${BACKEND_DIR}/venv"
PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.12}"
ENV_FILE="${BACKEND_DIR}/.env"

if [ ! -x "${PYTHON_BIN}" ]; then
  log "python interpreter not executable: ${PYTHON_BIN}"
  exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
  log "virtualenv not found, creating at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

log "installing backend dependencies"
"${VENV_DIR}/bin/pip" install --upgrade pip >/dev/null
"${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt" >/dev/null

if [ -f "${ENV_FILE}" ]; then
  log "loading environment variables from ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

log "running database migrations"
pushd "${BACKEND_DIR}" >/dev/null
FLASK_APP=run.py FLASK_ENV=production "${VENV_DIR}/bin/flask" db upgrade
popd >/dev/null

log "database migrations completed"
