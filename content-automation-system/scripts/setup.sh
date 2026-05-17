#!/usr/bin/env bash
# Phase 1 setup script — run once from the project root
# Usage: bash scripts/setup.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo ""
echo "================================================"
echo "  Choco Kitchen — Content Automation Setup"
echo "================================================"
echo ""

# ── 1. Python venv ────────────────────────────────
echo "▶ Step 1: Python virtual environment"
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "  Created venv/"
else
  echo "  venv/ already exists — skipping"
fi

source venv/bin/activate
echo "  Activated"

# ── 2. Dependencies ───────────────────────────────
echo ""
echo "▶ Step 2: Installing dependencies"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  All packages installed"

# ── 3. Redis ──────────────────────────────────────
echo ""
echo "▶ Step 3: Redis"

if command -v redis-cli &>/dev/null; then
  if redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo "  ✅ Redis is running"
  else
    echo "  Redis installed but not running — starting it..."
    brew services start redis 2>/dev/null || redis-server --daemonize yes
    sleep 1
    if redis-cli ping 2>/dev/null | grep -q "PONG"; then
      echo "  ✅ Redis started"
    else
      echo "  ❌ Could not start Redis — start it manually: brew services start redis"
    fi
  fi
else
  echo "  Redis not found — installing via Homebrew..."
  if command -v brew &>/dev/null; then
    brew install redis
    brew services start redis
    sleep 1
    echo "  ✅ Redis installed and started"
  else
    echo "  ❌ Homebrew not found. Install Redis manually:"
    echo "     macOS:  brew install redis && brew services start redis"
    echo "     Ubuntu: sudo apt-get install redis-server && sudo systemctl start redis"
  fi
fi

# ── 4. .env file ──────────────────────────────────
echo ""
echo "▶ Step 4: .env file"
if [ -f ".env" ]; then
  echo "  .env already exists — skipping copy"
else
  cp .env.example .env
  echo "  Created .env from .env.example"
  echo "  ⚠️  Open .env and fill in your real API keys before running the pipeline"
fi

# ── 5. data/cache dir ─────────────────────────────
echo ""
echo "▶ Step 5: Runtime directories"
mkdir -p data/cache logs
echo "  data/cache/ and logs/ ready"

# ── Done ──────────────────────────────────────────
echo ""
echo "================================================"
echo "  Setup complete!"
echo "================================================"
echo ""
echo "Next: fill in .env with your real API keys, then run:"
echo "  source venv/bin/activate"
echo "  python scripts/check_phase1.py"
echo ""
