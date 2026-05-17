import os
import sys
import base64
import requests
import redis
from dotenv import load_dotenv

load_dotenv()

PASS = "✅"
FAIL = "❌"


def test_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print(f"{FAIL} OpenRouter — OPENROUTER_API_KEY not set in .env")
        return False
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [{"role": "user", "content": "Say 'API works!'"}],
            },
            timeout=15,
        )
        if response.status_code == 200:
            print(f"{PASS} OpenRouter API connected")
            return True
        else:
            print(f"{FAIL} OpenRouter — HTTP {response.status_code}: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{FAIL} OpenRouter — network unreachable (no internet or DNS failed)")
        return False
    except requests.exceptions.Timeout:
        print(f"{FAIL} OpenRouter — request timed out")
        return False


def test_wordpress():
    url      = os.getenv("WORDPRESS_URL", "").rstrip("/")
    username = os.getenv("WORDPRESS_USERNAME", "")
    password = os.getenv("WORDPRESS_APP_PASSWORD", "")

    if not all([url, username, password]):
        print(f"{FAIL} WordPress — missing WORDPRESS_URL / USERNAME / APP_PASSWORD in .env")
        return False
    try:
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        response = requests.get(
            f"{url}/wp-json/wp/v2/posts",
            headers={"Authorization": f"Basic {auth}"},
            timeout=15,
        )
        if response.status_code == 200:
            print(f"{PASS} WordPress API connected ({url})")
            return True
        else:
            print(f"{FAIL} WordPress — HTTP {response.status_code}: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{FAIL} WordPress — could not reach {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"{FAIL} WordPress — request timed out")
        return False


def test_redis():
    try:
        r = redis.Redis(host="localhost", port=6379, db=0, socket_connect_timeout=3)
        r.set("test", "ok")
        val = r.get("test")
        if val == b"ok":
            print(f"{PASS} Redis connected (localhost:6379)")
            return True
        else:
            print(f"{FAIL} Redis — unexpected value: {val}")
            return False
    except redis.exceptions.ConnectionError:
        print(f"{FAIL} Redis — not running. Start it: brew services start redis")
        return False


if __name__ == "__main__":
    print("\n── Phase 1: API Connection Tests ──\n")
    r1 = test_openrouter()
    r2 = test_wordpress()
    r3 = test_redis()

    passed = sum([r1, r2, r3])
    print(f"\n{passed}/3 checks passed")

    if passed == 3:
        print("🎉 All APIs connected successfully!")
    else:
        print("Fix the ❌ items above, then re-run: python tests/test_apis.py")
        sys.exit(1)
