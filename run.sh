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
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  exit 0
}
trap cleanup SIGINT SIGTERM

BACKEND_PID=""

api_health_ok() {
  curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health 2>/dev/null | grep -q 200
}

port_8000_listening() {
  # macOS / Linux: من يستمع على 8000
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:8000 -sTCP:LISTEN -n -P >/dev/null 2>&1
    return $?
  fi
  return 1
}

echo "▶ الـ Backend (API) — http://127.0.0.1:8000"

if port_8000_listening && api_health_ok; then
  echo "✓ يوجد خادم يعمل مسبقاً على المنفذ 8000 — لن نُشغّل نسخة ثانية (تجنّب خطأ Address already in use)."
  echo "  لإيقاف القديم: lsof -i :8000 ثم kill <PID>"
elif port_8000_listening && ! api_health_ok; then
  echo "⚠ المنفذ 8000 مشغول ولكنه لا يستجيب لـ /api/health."
  echo "  أوقف العملية: lsof -i :8000  ثم  kill <PID>  أو غيّر المنفذ في backend."
  exit 1
else
  run_backend &
  BACKEND_PID=$!
fi

# انتظار جاهزية الـ Backend (حتى 30 ثانية)
echo "⏳ انتظار جاهزية الـ API..."
for i in $(seq 1 30); do
  if api_health_ok; then
    echo "✓ الـ Backend جاهز"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "⚠ تحذير: الـ Backend لم يستجب بعد. الواجهة ستفتح لكن قد ترى «تعذّر الاتصال بالخادم»."
  fi
  sleep 1
done

echo "▶ تشغيل الواجهة (Vite) — إن وُجد تعارض على 5173 سيجرّب منفذاً آخر تلقائياً"
run_frontend
