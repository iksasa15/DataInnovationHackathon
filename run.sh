#!/bin/bash
cd "$(dirname "$0")"

# إيقاف أي عملية قديمة على المنافذ
lsof -ti :8000 | xargs kill -9 2>/dev/null

echo "▶ تشغيل Backend (منفذ 8000)..."
cd backend && source .venv/bin/activate && python main.py &
BACKEND_PID=$!

echo "▶ تشغيل Frontend (منفذ 5173)..."
cd ../DataHackathon && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ Backend:  http://localhost:8000"
echo "✓ Frontend: http://localhost:5173"
echo ""
echo "اضغط Ctrl+C لإيقاف الاثنين"
wait
