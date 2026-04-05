#!/usr/bin/env bash
# IEC 62304: Verify engines are pure Python — no framework imports
# Usage: .agents/scripts/check_pure_python.sh

set -e

ENGINES_DIR="apps/backend/src/engines"
FOUND=0

echo "🔍 Checking for forbidden imports in engines..."

# Check for FastAPI imports
if grep -rn "from fastapi\|import fastapi" "$ENGINES_DIR" --include="*.py" 2>/dev/null; then
    echo "❌ FAIL: FastAPI imports found in engines/"
    FOUND=1
fi

# Check for SQLAlchemy imports
if grep -rn "from sqlalchemy\|import sqlalchemy" "$ENGINES_DIR" --include="*.py" 2>/dev/null; then
    echo "❌ FAIL: SQLAlchemy imports found in engines/"
    FOUND=1
fi

# Check for HTTP/network imports
if grep -rn "import requests\|from requests\|import httpx\|from httpx\|import aiohttp\|from aiohttp" "$ENGINES_DIR" --include="*.py" 2>/dev/null; then
    echo "❌ FAIL: Network imports found in engines/"
    FOUND=1
fi

# Check for random (non-deterministic)
if grep -rn "import random\|from random" "$ENGINES_DIR" --include="*.py" 2>/dev/null; then
    echo "❌ FAIL: Random imports found in engines/ (non-deterministic)"
    FOUND=1
fi

if [ $FOUND -eq 0 ]; then
    echo "✅ PASS: All engines are pure Python (no framework imports)"
    exit 0
else
    echo "❌ FAIL: IEC 62304 violation — engines must be pure Python"
    exit 1
fi
