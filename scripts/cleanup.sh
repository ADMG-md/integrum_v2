#!/usr/bin/env bash
# Integrum V2 — Cleanup Script
# Kills all development processes and frees ports

echo "=== Integrum V2 Cleanup ==="

# Kill backend on port 8000
BACKEND_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PID" ]; then
  echo "Killing backend processes: $BACKEND_PID"
  kill -9 $BACKEND_PID 2>/dev/null || true
else
  echo "No backend process on port 8000"
fi

# Kill frontend on port 3000
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$FRONTEND_PID" ]; then
  echo "Killing frontend processes: $FRONTEND_PID"
  kill -9 $FRONTEND_PID 2>/dev/null || true
else
  echo "No frontend process on port 3000"
fi

# Kill any stray uvicorn or next processes
STRAY_UVICORN=$(pgrep -f "uvicorn src.main" 2>/dev/null || true)
if [ -n "$STRAY_UVICORN" ]; then
  echo "Killing stray uvicorn processes: $STRAY_UVICORN"
  kill -9 $STRAY_UVICORN 2>/dev/null || true
fi

STRAY_NEXT=$(pgrep -f "next dev" 2>/dev/null || true)
if [ -n "$STRAY_NEXT" ]; then
  echo "Killing stray next processes: $STRAY_NEXT"
  kill -9 $STRAY_NEXT 2>/dev/null || true
fi

# Optional: stop docker compose if running
if [ -f "docker-compose.yml" ] && docker compose ps 2>/dev/null | grep -q "Up" 2>/dev/null; then
  echo "Stopping Docker Compose services..."
  docker compose down 2>/dev/null || true
fi

echo "=== Cleanup complete ==="
echo "Ports 8000, 3000, 5432, 6379 status:"
lsof -ti:8000 2>/dev/null && echo "  8000: OCCUPIED" || echo "  8000: FREE"
lsof -ti:3000 2>/dev/null && echo "  3000: OCCUPIED" || echo "  3000: FREE"
