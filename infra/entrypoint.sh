#!/usr/bin/env bash
set -euo pipefail

# 等待数据库就绪（Postgres）
if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL detected; waiting for database..."
  python - <<'PY'
import os, time, sys, socket
from urllib.parse import urlparse
db = os.environ.get("DATABASE_URL","")
if not db.startswith("postgres"):
    sys.exit(0)
u = urlparse(db.replace("postgresql+psycopg2://","postgres://"))
host, port = u.hostname, u.port or 5432
for i in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("DB reachable.")
            break
    except OSError:
        print("Waiting for DB...", i+1)
        time.sleep(2)
PY
fi

echo "Running migrations (skip heavy init)..."
export SKIP_HEAVY_INIT=1
python -m flask db upgrade
unset SKIP_HEAVY_INIT
echo "Migrations done."

echo "Starting Gunicorn..."
exec gunicorn -c infra/gunicorn.conf.py run:app
