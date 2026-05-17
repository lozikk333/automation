import base64
import mimetypes
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional


class WordPressPublisher:
    def __init__(self, site_url: str, username: str, app_password: str):
        self.site_url = site_url.rstrip("/")
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self._auth = self._make_auth(username, app_password)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _make_auth(self, username: str, password: str) -> str:
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return f"Basic {encoded}"

    def _json_headers(self) -> dict:
        return {"Authorization": self._auth, "Content-Type": "application/json"}

    # ------------------------------------------------------------------
    # Media
    # ------------------------------------------------------------------

    def upload_media_from_url(
        self,
        image_url: str,
        filename: str,
        alt_text: str = "",
        title: str = "",
    ) -> Dict:
        """Download image from a URL and upload it to the WordPress Media Library."""
        print(f"Downloading image: {image_url}")
        img_response = requests.get(image_url, timeout=60)
        img_response.raise_for_status()
        return self._upload_bytes(img_response.content, filename, alt_text, title)

    def upload_media_from_file(
        self,
        file_path: str,
        filename: Optional[str] = None,
        alt_text: str = "",
        title: str = "",
    ) -> Dict:
        """Upload a local file to the WordPress Media Library."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return self._upload_bytes(p.read_bytes(), filename or p.name, alt_text, title)

    def _upload_bytes(
        self,
        data: bytes,
        filename: str,
        alt_text: str,
        title: str,
    ) -> Dict:
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "image/jpeg"

        print(f"Uploading to WordPress Media Library: {filename}")
        response = requests.post(
            f"{self.api_base}/media",
            headers={
                "Authorization": self._auth,
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mime_type,
            },
            data=data,
            timeout=120,
        )
        response.raise_for_status()
        media = response.json()
        media_id = media["id"]

        if alt_text or title:
            self.update_media_metadata(media_id, alt_text=alt_text, title=title)

        return {
            "id": media_id,
            "source_url": media["source_url"],
            "alt_text": alt_text,
            "width": media.get("media_details", {}).get("width", 0),
            "height": media.get("media_details", {}).get("height", 0),
        }

    def update_media_metadata(
        self,
        media_id: int,
        alt_text: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict:
        updates = {}
        if alt_text is not None:
            updates["alt_text"] = alt_text
        if title is not None:
            updates["title"] = title
        if not updates:
            return {}

        response = requests.post(
            f"{self.api_base}/media/{media_id}",
            headers=self._json_headers(),
            json=updates,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def create_post(
        self,
        title: str,
        content: str,
        slug: str,
        meta_description: str,
        featured_image_id: int,
        category_ids: List[int],
        status: str = "draft",
        social_image_url: str = "",
        social_image_id: int = 0,
    ) -> Dict:
        """
        Create a WordPress post as draft or publish immediately.
        """
        status = status if status in {"draft", "publish"} else "draft"
        post_meta = {
            "rank_math_description": meta_description,
            "_yoast_wpseo_metadesc": meta_description,
        }
        if social_image_url:
            post_meta.update({
                # Rank Math and Yoast social image fields. These keep the
                # on-page featured image unchanged while giving social/RSS
                # consumers a pin-first image to read from post metadata.
                "rank_math_facebook_image": social_image_url,
                "rank_math_twitter_image": social_image_url,
                "_yoast_wpseo_opengraph-image": social_image_url,
                "_yoast_wpseo_twitter-image": social_image_url,
                "_automation_social_image": social_image_url,
                "_automation_rss_image": social_image_url,
            })
        if social_image_id:
            post_meta.update({
                "rank_math_facebook_image_id": str(social_image_id),
                "rank_math_twitter_image_id": str(social_image_id),
                "_thumbnail_id_rss": str(social_image_id),
                "_automation_social_image_id": str(social_image_id),
            })

        post_data = {
            "title": title,
            "content": content,
            "slug": slug,
            "status": status,
            "featured_media": featured_image_id,
            "categories": category_ids,
            "meta": post_meta,
        }

        response = requests.post(
            f"{self.api_base}/posts",
            headers=self._json_headers(),
            json=post_data,
            timeout=60,
        )
        response.raise_for_status()
        post = response.json()

        print(f"Post created: [{post['status']}] {post['link']}")
        return {
            "id": post["id"],
            "link": post["link"],
            "slug": post["slug"],
            "status": post["status"],
            "featured_media": post.get("featured_media"),
        }

    def update_post(self, post_id: int, **fields) -> Dict:
        """Patch any fields on an existing post (e.g. status → 'publish')."""
        response = requests.post(
            f"{self.api_base}/posts/{post_id}",
            headers=self._json_headers(),
            json=fields,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Categories — read-only, never creates new ones
    # ------------------------------------------------------------------

    FALLBACK_CATEGORY_ID = 1  # WordPress default "Uncategorized"

    def fetch_categories(self) -> List[Dict]:
        """Return all existing categories from WordPress as id/name/slug objects."""
        categories: List[Dict] = []
        try:
            page = 1
            while True:
                response = requests.get(
                    f"{self.api_base}/categories",
                    params={"per_page": 100, "page": page},
                    timeout=30,
                )
                response.raise_for_status()
                items = response.json()
                if not isinstance(items, list) or not items:
                    break
                for item in items:
                    if item.get("id") and item.get("name") and item.get("slug"):
                        categories.append({
                            "id": int(item["id"]),
                            "name": str(item["name"]),
                            "slug": str(item["slug"]),
                        })
                total_pages = int(response.headers.get("X-WP-TotalPages") or 1)
                if page >= total_pages:
                    break
                page += 1
            return categories
        except requests.RequestException as e:
            print(f"Warning: could not fetch categories ({e}) — using fallback id={self.FALLBACK_CATEGORY_ID}")
            return []

    def _category_text(self, category: Dict) -> str:
        return f"{category.get('name', '')} {category.get('slug', '')}".lower()

    def _tokens(self, text: str) -> set[str]:
        tokens = set()
        for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
            tokens.add(token)
            if len(token) > 3 and token.endswith("s"):
                tokens.add(token[:-1])
        return tokens

    def _find_category_by_terms(self, categories: List[Dict], terms: tuple[str, ...]) -> Optional[int]:
        for term in terms:
            for cat in categories:
                if term in self._category_text(cat):
                    print(f"Category fallback selected: '{cat['name']}' (id={cat['id']}, term={term})")
                    return cat["id"]
        return None

    def select_best_category(
        self,
        keyword: str,
        categories: List[Dict],
        title: str = "",
        recipe_category: str = "",
    ) -> int:
        """
        Return the ID of the most relevant existing category.
        Uses keyword, title, recipe card category, and recipe-specific rules.
        Never falls back to the first category, because that can misclassify
        cake/dessert posts as Breakfast when Breakfast happens to be first.
        """
        if not categories:
            return self.FALLBACK_CATEGORY_ID

        context = f"{keyword} {title} {recipe_category}".lower()
        context_tokens = self._tokens(context)

        dessert_signals = {
            "cake", "cakes", "cupcake", "cupcakes", "cheesecake", "brownie",
            "brownies", "cookie", "cookies", "dessert", "desserts", "chocolate",
            "sweet", "pie", "pies", "pudding", "muffin", "muffins", "banana",
        }
        breakfast_signals = {
            "breakfast", "pancake", "pancakes", "waffle", "waffles", "oatmeal",
            "eggs", "omelet", "omelette", "toast", "smoothie",
        }

        wanted_terms: list[str] = []
        if context_tokens & dessert_signals or "dessert" in recipe_category.lower():
            wanted_terms.extend(["cake", "cakes", "dessert", "desserts", "baking", "sweets"])
        if context_tokens & breakfast_signals or "breakfast" in recipe_category.lower():
            wanted_terms.extend(["breakfast", "brunch"])

        best_id    = None
        best_score = 0

        for cat in categories:
            cat_text = self._category_text(cat)
            cat_words = self._tokens(cat_text)
            score = len(context_tokens & cat_words) * 2

            for term in wanted_terms:
                if term in cat_text:
                    score += 10

            # Avoid Breakfast for desserts/cakes unless the context is truly breakfast.
            if "breakfast" in cat_text and (context_tokens & dessert_signals) and not (context_tokens & breakfast_signals):
                score -= 8

            # Also check if any important context word appears inside the category name.
            if score == 0:
                for word in context_tokens:
                    if len(word) > 3 and word in cat_text:
                        score += 1

            if score > best_score:
                best_score = score
                best_id    = cat["id"]

        if best_id and best_score > 0:
            matched_name = next(c["name"] for c in categories if c["id"] == best_id)
            print(f"Category selected: '{matched_name}' (id={best_id}, score={best_score})")
            return best_id

        fallback_id = self._find_category_by_terms(categories, ("dessert", "desserts", "cake", "cakes"))
        if fallback_id:
            return fallback_id

        print(f"No category match for '{keyword}' — using fallback id={self.FALLBACK_CATEGORY_ID}")
        return self.FALLBACK_CATEGORY_ID

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def seo_filename(self, slug: str, image_type: str = "hero") -> str:
        """Return an SEO-friendly filename: <slug>-<type>.jpg"""
        return f"{slug}-{image_type}.jpg"

    def verify_connection(self) -> bool:
        """Quick auth check — returns True if credentials are valid."""
        try:
            response = requests.get(
                f"{self.api_base}/users/me",
                headers={"Authorization": self._auth},
                timeout=15,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
