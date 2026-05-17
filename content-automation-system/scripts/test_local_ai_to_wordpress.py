"""
Test pipeline: Local AI (Ollama) → WordPress
Run: python scripts/test_local_ai_to_wordpress.py
"""

import requests
import base64

# ── Config ────────────────────────────────────────
LOCAL_AI_URL  = "http://localhost:11434"
MODEL_NAME    = "qwen3.5"

WORDPRESS_URL = "https://newrecipetoday.com"
USERNAME      = "recipesnora9@gmail.com"
PASSWORD      = "dZmC MljA TEDE AOIE jt5G pfDs"

KEYWORD       = "easy chocolate cake"
# ─────────────────────────────────────────────────


def generate_article_local(keyword: str) -> str | None:
    prompt = (
        f"Write a 300-600 word blog article about {keyword} "
        f"in simple HTML using <h2> and <p> tags"
    )
    try:
        response = requests.post(
            f"{LOCAL_AI_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        if not text:
            print("❌ Local AI returned an empty response")
            return None
        return text

    except requests.exceptions.ConnectionError:
        print("❌ Ollama not running, run: ollama serve")
        return None
    except requests.exceptions.Timeout:
        print("❌ Ollama timed out — model may still be loading, try again")
        return None
    except Exception as e:
        print(f"❌ Local AI error: {e}")
        return None


def publish_to_wordpress(title: str, content: str) -> dict | None:
    token = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    try:
        response = requests.post(
            f"{WORDPRESS_URL.rstrip('/')}/wp-json/wp/v2/posts",
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            },
            json={"title": title, "content": content, "status": "draft"},
            timeout=30,
        )
        if response.status_code == 401:
            print("❌ Invalid WordPress credentials — check USERNAME and PASSWORD")
            return None
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"❌ WordPress error: {e}")
        print(f"   Response: {response.text[:300]}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot reach WordPress at {WORDPRESS_URL}")
        return None
    except Exception as e:
        print(f"❌ WordPress error: {e}")
        return None


# ── Main ──────────────────────────────────────────
print(f"Keyword : {KEYWORD}")
print(f"Model   : {MODEL_NAME} @ {LOCAL_AI_URL}")
print(f"Site    : {WORDPRESS_URL}\n")

print("Step 1: Generating article...")
content = generate_article_local(KEYWORD)
if not content:
    exit(1)
print(f"✅ Article generated ({len(content.split())} words)\n")

print("Step 2: Publishing to WordPress as draft...")
result = publish_to_wordpress(title=KEYWORD.title(), content=content)
if not result:
    exit(1)

print("✅ Article sent successfully")
if result.get("link"):
    print(f"   Link: {result['link']}")
