import argparse
import os
import re
from html import unescape

import requests
from dotenv import load_dotenv

from content_engine.recipe_card import build_tasty_shortcode, inject_into_content
from orchestrator.state_manager import StateManager
from publishers.wordpress import WordPressPublisher


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def section_after_heading(html: str, heading_words: tuple[str, ...], tag: str) -> str:
    headings = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S))
    for index, match in enumerate(headings):
        heading = strip_tags(match.group(1)).lower()
        if any(word in heading for word in heading_words):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(html)
            section = html[match.end():end]
            tag_match = re.search(fr"<{tag}\b[^>]*>.*?</{tag}>", section, re.I | re.S)
            if tag_match:
                return tag_match.group(0).strip()
    return ""


def paragraph_after_heading(html: str, heading_words: tuple[str, ...]) -> str:
    headings = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html, re.I | re.S))
    for index, match in enumerate(headings):
        heading = strip_tags(match.group(1)).lower()
        if any(word in heading for word in heading_words):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(html)
            section = html[match.end():end]
            p_match = re.search(r"<p\b[^>]*>.*?</p>", section, re.I | re.S)
            if p_match:
                return strip_tags(p_match.group(0))
    return ""


def infer_recipe(article_html: str, title: str, keyword: str, meta_desc: str) -> dict:
    ingredients = section_after_heading(article_html, ("ingredient",), "ul")
    instructions = section_after_heading(article_html, ("instruction", "step"), "ol")
    notes = section_after_heading(article_html, ("tip", "trick", "pro"), "ul")

    if not ingredients:
        raise ValueError("Could not find an ingredients <ul> section")
    if not instructions:
        raise ValueError("Could not find an instructions <ol> section")
    if not notes:
        notes = "<ul><li>Dry ingredients well before mixing or cooking for the best texture.</li><li>Chill or rest the recipe as directed before serving.</li></ul>"

    description = meta_desc or paragraph_after_heading(article_html, ("secret", "morning", "best", "copycat"))
    description = unescape(description or f"A helpful homemade recipe for {keyword}.")

    lower = article_html.lower()
    prep = "15 mins" if "fifteen" in lower or "15" in lower else "20 mins"
    cook = "0 mins" if "no bake" in lower or "salad" in lower else "20 mins"
    total = "15 mins" if cook == "0 mins" else "40 mins"
    method = "No-Cook" if cook == "0 mins" else "Cooking"
    category = "Dessert" if "dessert" in lower or "sweet" in lower else "Main Course"

    return {
        "Description": description[:300],
        "Ingredients": ingredients,
        "Instructions": instructions,
        "Notes": notes,
        "Details": {
            "Prep Time": prep,
            "Cook Time": cook,
            "Total Time": total,
            "Yield": "6 servings",
            "Category": category,
            "Method": method,
            "Cuisine": "American",
            "Diet": "Vegetarian" if "grape salad" in lower else "Halal",
        },
        "Keywords": keyword,
        "Nutrition": {
            "Serving Size": "1 serving",
            "Calories": "320",
            "Sugar": "24g",
            "Sodium": "120mg",
            "Fat": "18g",
            "Saturated Fat": "9g",
            "Unsaturated Fat": "8g",
            "Trans Fat": "0g",
            "Carbohydrates": "38g",
            "Fiber": "2g",
            "Protein": "4g",
            "Cholesterol": "35mg",
        },
    }


def get_post(post_id: int) -> dict:
    wp_url = os.getenv("WORDPRESS_URL").rstrip("/")
    response = requests.get(
        f"{wp_url}/wp-json/wp/v2/posts/{post_id}",
        params={"context": "edit"},
        auth=(os.getenv("WORDPRESS_USERNAME"), os.getenv("WORDPRESS_APP_PASSWORD")),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("id", type=int)
    parser.add_argument("--post", action="store_true", help="Treat id as a WordPress post id instead of a dashboard job id")
    args = parser.parse_args()

    load_dotenv()
    state = StateManager("data/state.db")

    job_id = None
    artifacts = {}
    if args.post:
        post_id = args.id
        post = get_post(post_id)
        article_html = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered") or ""
        title = post.get("title", {}).get("raw") or post.get("title", {}).get("rendered") or f"Post {post_id}"
        keyword = title
        meta_desc = ""
    else:
        job_id = args.id
        job = state.get_job_detail(job_id)
        if not job:
            raise SystemExit(f"Job {job_id} not found")

        artifacts = job.get("artifacts", {})
        post_id = int(artifacts.get("wp_post_id") or job.get("metadata", {}).get("wp_post_id") or 0)
        if not post_id:
            raise SystemExit(f"Job {job_id} has no wp_post_id")

        article_html = artifacts.get("article_html") or ""
        title = artifacts.get("article_title") or job["keyword"]
        keyword = job["keyword"]
        meta_desc = artifacts.get("article_meta_desc") or ""

    if "tasty-recipe id=" in article_html:
        print(f"Post {post_id} already has a recipe shortcode")
        return

    recipe = artifacts.get("recipe_json")
    if not isinstance(recipe, dict) or not recipe:
        recipe = infer_recipe(
            article_html=article_html,
            title=title,
            keyword=keyword,
            meta_desc=meta_desc,
        )

    shortcode = build_tasty_shortcode(
        recipe=recipe,
        title=title,
        wp_url=os.getenv("WORDPRESS_URL"),
        username=os.getenv("WORDPRESS_USERNAME"),
        password=os.getenv("WORDPRESS_APP_PASSWORD"),
        image_url=artifacts.get("midjourney_image_url") or "",
        media_id=0,
    )
    if not shortcode:
        raise SystemExit("Could not create Tasty Recipe shortcode")

    updated_html = inject_into_content(shortcode, article_html)
    wp = WordPressPublisher(
        os.getenv("WORDPRESS_URL"),
        os.getenv("WORDPRESS_USERNAME"),
        os.getenv("WORDPRESS_APP_PASSWORD"),
    )
    wp.update_post(post_id, content=updated_html)

    if job_id:
        state.save_artifact(job_id, "recipe_json", recipe)
        state.save_artifact(job_id, "tasty_recipe_shortcode", shortcode)
        state.save_artifact(job_id, "article_html", updated_html)
        state.log_dashboard(job_id, "info", "repair", f"Recipe card added to WordPress post #{post_id}: {shortcode}")
        print(f"Added {shortcode} to job {job_id}, post {post_id}")
    else:
        state.log_dashboard(None, "info", "repair", f"Recipe card added to WordPress post #{post_id}: {shortcode}")
        print(f"Added {shortcode} to post {post_id}")


if __name__ == "__main__":
    main()
