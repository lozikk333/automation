"""
Test pipeline: NVIDIA AI API → WordPress
Run: python scripts/test_nvidia_api_to_wordpress.py
"""

import requests
import base64

# ── Config ────────────────────────────────────────
API_URL  = "https://integrate.api.nvidia.com/v1/chat/completions"
API_KEY  = "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"
MODEL    = "google/gemma-4-31b-it"

WORDPRESS_URL = "YOUR_WORDPRESS_URL"
USERNAME      = "YOUR_USERNAME"
PASSWORD      = "YOUR_APPLICATION_PASSWORD"

KEYWORD = "easy chocolate cake"
# ─────────────────────────────────────────────────


def generate_article_api(keyword: str) -> str | None:
    prompt = (
        f"Write a 300-600 word blog article about {keyword} "
        f"in simple HTML using <h2> and <p> tags"
    )
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
        if not text:
            print("❌ API returned empty response")
            return None
        return text

    except requests.exceptions.ConnectionError:
        print("❌ Cannot reach NVIDIA API — check your internet connection")
        return None
    except requests.exceptions.Timeout:
        print("❌ NVIDIA API timed out")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ API error: {e}")
        print(f"   Response: {response.text[:300]}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
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
print(f"Model   : {MODEL}")
print(f"Site    : {WORDPRESS_URL}\n")

print("Step 1: Generating article via NVIDIA API...")
content = generate_article_api(KEYWORD)
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
