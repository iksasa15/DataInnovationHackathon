#!/usr/bin/env bash
# تشغيل الـ Backend (FastAPI) فقط — المنفذ 8000

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"

if [ -d ".venv" ]; then
  . .venv/bin/activate
fi

echo "▶ تشغيل الـ Backend على http://127.0.0.1:8000"
exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
