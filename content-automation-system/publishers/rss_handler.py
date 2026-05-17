"""
RSS Feed Handler

WordPress automatically manages the RSS feed.
Publishing a post via the REST API (status='publish') instantly adds
it to /feed/ — no extra steps required.

This module provides helpers to verify and inspect the feed.
"""

import requests
from typing import Dict


class RSSFeedHandler:
    """
    Feed URLs available after publishing to chocokitchen.com:

      Main feed:      https://chocokitchen.com/feed/
      Category feed:  https://chocokitchen.com/category/<slug>/feed/
      JSON endpoint:  https://chocokitchen.com/wp-json/wp/v2/posts
    """

    def __init__(self, wordpress_url: str):
        self.base_url = wordpress_url.rstrip("/")

    def feed_url(self, category_slug: str = None) -> str:
        if category_slug:
            return f"{self.base_url}/category/{category_slug}/feed/"
        return f"{self.base_url}/feed/"

    def verify(self) -> Dict:
        """Check that the RSS feed is live and returning XML."""
        url = self.feed_url()
        try:
            response = requests.get(url, timeout=10)
            content_type = response.headers.get("Content-Type", "")
            body_start = response.text[:200]
            is_feed = (
                response.status_code == 200
                and ("xml" in content_type or "<rss" in body_start or "<feed" in body_start)
            )
            if is_feed:
                return {"status": "active", "feed_url": url, "message": "RSS feed is live"}
            return {
                "status": "error",
                "feed_url": url,
                "message": f"Unexpected response: HTTP {response.status_code}, Content-Type: {content_type}",
            }
        except requests.RequestException as exc:
            return {"status": "error", "feed_url": url, "message": str(exc)}

    def latest_post_in_feed(self) -> Dict:
        """Return the title and link of the most recent post in the RSS feed."""
        import xml.etree.ElementTree as ET

        url = self.feed_url()
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        item = root.find("./channel/item")
        if item is None:
            return {}

        return {
            "title": item.findtext("title", ""),
            "link": item.findtext("link", ""),
            "pub_date": item.findtext("pubDate", ""),
        }
