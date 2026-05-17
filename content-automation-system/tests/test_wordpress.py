"""
Integration test for WordPressPublisher — requires a live chocokitchen.com connection.

Run:
    source venv/bin/activate
    python tests/test_wordpress.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from PIL import Image
from publishers.wordpress import WordPressPublisher

load_dotenv()

WP_URL      = os.getenv("WORDPRESS_URL")
WP_USER     = os.getenv("WORDPRESS_USERNAME")
WP_PASS     = os.getenv("WORDPRESS_APP_PASSWORD")
SITE_DOMAIN = WP_URL.rstrip("/") if WP_URL else ""


def make_wp() -> WordPressPublisher:
    assert WP_URL and WP_USER and WP_PASS, "Missing WORDPRESS_* env vars in .env"
    return WordPressPublisher(WP_URL, WP_USER, WP_PASS)


def test_connection():
    print("--- Connection ---")
    wp = make_wp()
    assert wp.verify_connection(), "WordPress auth failed — check credentials"
    print("✅ Connection OK")


def test_upload_from_url():
    print("\n--- Upload from URL ---")
    wp = make_wp()
    result = wp.upload_media_from_url(
        image_url="https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800",
        filename="test-choco-hero.jpg",
        alt_text="Test chocolate hero image",
        title="Test Hero",
    )
    print(f"Media ID:  {result['id']}")
    print(f"URL:       {result['source_url']}")
    print(f"Size:      {result['width']}×{result['height']}")
    assert result["source_url"].startswith(SITE_DOMAIN), \
        f"Image URL must start with {SITE_DOMAIN}, got: {result['source_url']}"
    print("✅ upload_media_from_url OK")
    return result["id"]


def test_upload_from_file():
    print("\n--- Upload from local file ---")
    wp = make_wp()

    # Create a minimal 1200×800 test image
    tmp_path = "/tmp/test-choco-hero-local.jpg"
    Image.new("RGB", (1200, 800), color=(80, 40, 10)).save(tmp_path, quality=85)

    result = wp.upload_media_from_file(
        file_path=tmp_path,
        filename="test-choco-hero-local.jpg",
        alt_text="Test local upload",
        title="Test Local Hero",
    )
    print(f"Media ID:  {result['id']}")
    print(f"URL:       {result['source_url']}")
    assert result["source_url"].startswith(SITE_DOMAIN), \
        f"Image URL must start with {SITE_DOMAIN}"
    print("✅ upload_media_from_file OK")
    return result["id"]


def test_create_draft_post(featured_media_id: int):
    print("\n--- Create draft post ---")
    wp = make_wp()

    cat_id = wp.get_or_create_category("Chocolate Cakes")
    print(f"Category ID: {cat_id}")

    result = wp.create_post(
        title="Test: Best Chocolate Lava Cake Recipe",
        content="<h2>Introduction</h2>\n<p>This is a test post created by the automation system.</p>",
        slug="test-chocolate-lava-cake-automation",
        meta_description="Learn how to make the best chocolate lava cake in under 30 minutes. Rich, gooey, and easy.",
        featured_image_id=featured_media_id,
        category_ids=[cat_id],
        status="draft",
    )
    print(f"Post ID:   {result['id']}")
    print(f"Status:    {result['status']}")
    print(f"Link:      {result['link']}")
    assert result["status"] == "draft"
    assert result["featured_media"] == featured_media_id
    print("✅ create_post OK")
    return result["id"]


def test_seo_filename():
    print("\n--- SEO filename ---")
    wp = make_wp()
    name = wp.seo_filename("chocolate-lava-cake", "hero")
    assert name == "chocolate-lava-cake-hero.jpg"
    print(f"Filename: {name}")
    print("✅ seo_filename OK")


if __name__ == "__main__":
    test_connection()
    media_id = test_upload_from_url()
    test_upload_from_file()
    test_create_draft_post(media_id)
    test_seo_filename()
    print("\n🎉 All WordPress checks passed!")
