"""
Phase 1 verification script.
Checks every item on the Phase 1 completion checklist and prints a clear pass/fail report.

Run:
    source venv/bin/activate
    python scripts/check_phase1.py
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []

def check(label, passed, detail=""):
    icon = PASS if passed else FAIL
    results.append((passed, label, detail))
    status = f"{icon}  {label}"
    if detail:
        status += f"\n      {detail}"
    print(status)


print()
print("=" * 52)
print("  Phase 1 Checklist — Verification")
print("=" * 52)
print()

# ── 1. Project structure ──────────────────────────
required_dirs = [
    "orchestrator", "content_engine", "image_engine",
    "compositor", "publishers", "utils", "database",
    "templates/fonts", "data/cache", "logs", "tests",
    "scripts", "static",
]
missing = [d for d in required_dirs if not (ROOT / d).is_dir()]
check(
    "Project structure — all folders present",
    not missing,
    f"Missing: {missing}" if missing else "",
)

# ── 2. Python venv + dependencies ────────────────
venv_python = ROOT / "venv" / "bin" / "python"
check(
    "venv exists",
    venv_python.exists(),
    str(venv_python) if not venv_python.exists() else "",
)

required_packages = ["fastapi", "celery", "redis", "PIL", "requests", "httpx", "dotenv", "pydantic", "uvicorn"]
missing_pkgs = []
for pkg in required_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing_pkgs.append(pkg)
check(
    "All dependencies installed",
    not missing_pkgs,
    f"Missing packages: {missing_pkgs}" if missing_pkgs else "",
)

# ── 3. Redis ─────────────────────────────────────
redis_installed = subprocess.run(["which", "redis-cli"], capture_output=True).returncode == 0
check(
    "Redis installed",
    redis_installed,
    "Install: brew install redis" if not redis_installed else "",
)

redis_running = False
if redis_installed:
    try:
        result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, timeout=3)
        redis_running = result.stdout.strip() == "PONG"
    except Exception:
        pass
check(
    "Redis running (redis-cli ping → PONG)",
    redis_running,
    "Start: brew services start redis" if not redis_running else "",
)

# ── 4. .env file with required keys ──────────────
env_path = ROOT / ".env"
check(
    ".env file exists",
    env_path.exists(),
    "Run: cp .env.example .env  then fill in your keys" if not env_path.exists() else "",
)

required_keys = ["OPENROUTER_API_KEY", "WORDPRESS_URL", "WORDPRESS_USERNAME", "WORDPRESS_APP_PASSWORD"]
if env_path.exists():
    env_contents = env_path.read_text()
    filled = []
    empty  = []
    for key in required_keys:
        val = ""
        for line in env_contents.splitlines():
            if line.startswith(key + "="):
                val = line.split("=", 1)[1].strip()
        if val and "xxxx" not in val and val != "":
            filled.append(key)
        else:
            empty.append(key)
    check(
        ".env has all 4 required keys filled in",
        not empty,
        f"Still placeholder: {empty}" if empty else "",
    )
    imgbb = "imgbb" in env_contents.lower() or "IMGBB" in env_contents
    pinterest = "PINTEREST" in env_contents
    check(
        "No external service credentials (no ImgBB, no Pinterest)",
        not imgbb and not pinterest,
        "Remove ImgBB or Pinterest keys from .env" if (imgbb or pinterest) else "",
    )
else:
    check(".env has all 4 required keys filled in", False, ".env missing")
    check("No external service credentials", False, ".env missing")

# ── 5. test_apis.py exists ────────────────────────
test_path = ROOT / "tests" / "test_apis.py"
check(
    "tests/test_apis.py exists",
    test_path.exists(),
)

# ── 6. Live API test (optional, requires real keys) ──
print()
print("── Live API Test (requires real keys + Redis) ──")
try:
    run_live = input("Run live test_apis.py now? [y/N]: ").strip().lower() == "y"
except EOFError:
    run_live = False
if run_live:
    result = subprocess.run(
        [sys.executable, str(test_path)],
        capture_output=False,
        cwd=str(ROOT),
    )
    check("test_apis.py passes all checks", result.returncode == 0)
else:
    print(f"  Skipped — run manually: python tests/test_apis.py")

# ── Summary ───────────────────────────────────────
print()
print("=" * 52)
passed = sum(1 for r in results if r[0])
total  = len(results)
print(f"  {passed}/{total} checks passed")
if passed == total:
    print("  🎉 Phase 1 complete!")
else:
    failed = [r[1] for r in results if not r[0]]
    print(f"  Fix these: {failed}")
print("=" * 52)
print()
