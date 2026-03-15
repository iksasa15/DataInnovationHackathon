#!/usr/bin/env bash
# سكربت تشغيل مشروع Data Innovation Hackathon (الواجهة + الـ API)

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# تشغيل الـ Backend (FastAPI)
run_backend() {
  cd "$ROOT/backend"
  if [ -d ".venv" ]; then
    . .venv/bin/activate
  fi
  exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

# تشغيل الواجهة (Vue + Vite)
run_frontend() {
  cd "$ROOT/DataHackathon"
  exec npm run dev
}

# إيقاف العمليات عند الخروج (Ctrl+C)
cleanup() {
  echo ""
  echo "إيقاف التشغيل..."
  kill $BACKEND_PID 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "▶ تشغيل الـ Backend (API) على http://127.0.0.1:8000"
run_backend &
BACKEND_PID=$!

# انتظار جاهزية الـ Backend (حتى 30 ثانية)
echo "⏳ انتظار تشغيل الـ Backend..."
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null | grep -q 200; then
    echo "✓ الـ Backend جاهز"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "⚠ تحذير: الـ Backend لم يستجب بعد. الواجهة ستفتح لكن قد ترى «تعذّر الاتصال بالخادم» حتى يعمل الـ Backend."
  fi
  sleep 1
done

echo "▶ تشغيل الواجهة (Vue) على http://localhost:5173"
run_frontend
