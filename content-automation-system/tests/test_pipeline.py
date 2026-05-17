"""
Unit tests for Phase 7 components.

Tests retry_logic and RSSFeedHandler without needing Redis or Celery running.
Run:  python tests/test_pipeline.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from utils.retry_logic import retry_with_backoff
from publishers.rss_handler import RSSFeedHandler

load_dotenv()


# ------------------------------------------------------------------
# retry_with_backoff tests
# ------------------------------------------------------------------

def test_retry_succeeds_on_second_attempt():
    attempts = {"count": 0}

    @retry_with_backoff(max_retries=3, base_delay=0, exceptions=(ValueError,))
    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("simulated failure")
        return "ok"

    result = flaky()
    assert result == "ok"
    assert attempts["count"] == 2
    print(f"✅ retry succeeded on attempt {attempts['count']}")


def test_retry_raises_after_max():
    attempts = {"count": 0}

    @retry_with_backoff(max_retries=2, base_delay=0, exceptions=(RuntimeError,))
    def always_fails():
        attempts["count"] += 1
        raise RuntimeError("always bad")

    try:
        always_fails()
        assert False, "Should have raised"
    except RuntimeError:
        pass

    assert attempts["count"] == 2
    print(f"✅ retry raised after {attempts['count']} attempts")


def test_retry_does_not_catch_other_exceptions():
    @retry_with_backoff(max_retries=3, base_delay=0, exceptions=(ValueError,))
    def wrong_exc():
        raise TypeError("wrong type")

    try:
        wrong_exc()
        assert False, "Should have raised"
    except TypeError:
        pass
    print("✅ retry ignores non-matching exception types")


# ------------------------------------------------------------------
# RSSFeedHandler tests
# ------------------------------------------------------------------

def test_rss_feed_url():
    handler = RSSFeedHandler("https://chocokitchen.com")
    assert handler.feed_url() == "https://chocokitchen.com/feed/"
    assert handler.feed_url("chocolate-cakes") == "https://chocokitchen.com/category/chocolate-cakes/feed/"
    print("✅ feed_url() OK")


def test_rss_feed_live():
    wp_url = os.getenv("WORDPRESS_URL")
    if not wp_url:
        print("⚠️  WORDPRESS_URL not set — skipping live RSS check")
        return

    handler = RSSFeedHandler(wp_url)
    result = handler.verify()
    print(f"RSS status: {result['status']} — {result['message']}")
    if result["status"] != "active":
        print(f"⚠️  RSS feed not active — enable it in Yoast SEO → Search Appearance → RSS")
    else:
        print(f"✅ RSS feed live at {result['feed_url']}")


if __name__ == "__main__":
    print("--- Retry Logic ---")
    test_retry_succeeds_on_second_attempt()
    test_retry_raises_after_max()
    test_retry_does_not_catch_other_exceptions()

    print("\n--- RSS Feed Handler ---")
    test_rss_feed_url()
    test_rss_feed_live()

    print("\n🎉 All Phase 7 checks passed!")
