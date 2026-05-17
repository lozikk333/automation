"""
Recipe card integration for Tasty Recipes WordPress plugin.

Flow:
    article_html
        → generate_recipe_json()     (AI fills JSON from article)
        → build_tasty_shortcode()    (creates WP tasty_recipe post → returns shortcode string)
        → inject_into_content()      (inserts shortcode before FAQ, or at end)
"""

import asyncio
import time
import requests
import base64
from .llm_client import LLMClient


# ── AI prompt (user's exact template) ────────────────────────────────

RECIPE_PROMPT = (
    "Fill this json in English language based on the article "
    "and complete missed info in the json and only reply with the json fully filled:\n"
    '{\n'
    '"Description": "brief describtion",\n'
    '"Ingredients": "list of ingredient with quantity in ul tag of html",\n'
    '"Instructions": "lnumbered ist of Instructions in ol tag of html",\n'
    '"Notes": "list of Notes in ul tag of html",\n'
    '"Details": {\n'
    '    "Prep Time":"",\n'
    '    "Cook Time":"",\n'
    '    "Total Time":"",\n'
    '    "Yield":"",\n'
    '    "Category":"",\n'
    '    "Method":"",\n'
    '    "Cuisine":"",\n'
    '    "Diet":"choose one of this (Diabetic,Gluten Free,Halal,Hindu,Kosher,Low Calorie,Low Fat,Low Lactose,Low Salt,Vegan,Vegetarian)"\n'
    '    },\n'
    '"Keywords": "",\n'
    '"Nutrition": {\n'
    '    "Serving Size":"",\n'
    '    "Calories":"",\n'
    '    "Sugar":"",\n'
    '    "Sodium":"",\n'
    '    "Fat":"",\n'
    '    "Saturated Fat":"",\n'
    '    "Unsaturated Fat":"",\n'
    '    "Trans Fat":"",\n'
    '    "Carbohydrates":"",\n'
    '    "Fiber":"",\n'
    '    "Protein":"",\n'
    '    "Cholesterol":""}\n'
    '}\n\n'
    "Article:\n{article_content}"
)


# ── Step 1: Generate recipe JSON ──────────────────────────────────────

def generate_recipe_json(article_content: str, api_key: str, title: str = "") -> dict | None:
    """
    Use AI to fill the recipe JSON template from article content.
    Retries up to 4× on any failure (429, parse error, network error).
    Returns dict or None on failure (pipeline continues safely).
    """
    llm    = LLMClient(api_key)
    prompt = RECIPE_PROMPT.replace("{article_content}", article_content[:4000])

    # wait times between retries: 30s, 45s, 60s
    waits = [30, 45, 60]

    for attempt in range(1, 5):
        try:
            print(f"[recipe] ── Attempt {attempt}/4: generating recipe JSON ──")
            raw = asyncio.run(llm.generate(prompt, temperature=0.3, max_tokens=2000))
            print(f"[recipe] Raw LLM response length: {len(raw)} chars")
            print(f"[recipe] Raw LLM preview: {raw[:300]}")
            recipe = llm.parse_json(raw)
            print(f"[recipe] Recipe JSON keys: {list(recipe.keys())}")
            print(f"[recipe] Recipe JSON generated ✅")
            return recipe

        except Exception as e:
            err = str(e)
            print(f"[recipe] Attempt {attempt} FAILED: {type(e).__name__}: {err[:200]}")

            if attempt < 4:
                wait = waits[attempt - 1]
                if "429" in err:
                    print(f"[recipe] Rate limited — waiting {wait}s before retry...")
                else:
                    print(f"[recipe] Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"[recipe] All 4 attempts failed — skipping recipe card")
                return None

    return None


# ── Step 2: Create WP post + return shortcode string ─────────────────

def build_tasty_shortcode(
    recipe: dict,
    title: str,
    wp_url: str,
    username: str,
    password: str,
    image_url: str = "",
    media_id: int = 0,
) -> str | None:
    """
    Create a tasty_recipe WordPress post and return the shortcode string.
    Returns '[tasty-recipe id="X"]' or None on failure.
    """
    d = recipe.get("Details", {})
    n = recipe.get("Nutrition", {})

    auth    = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}

    payload = {
        "title":          title,
        "status":         "publish",
        "featured_media": media_id,
        "meta": {
            "description":     recipe.get("Description", ""),
            "ingredients":     recipe.get("Ingredients", ""),
            "instructions":    recipe.get("Instructions", ""),
            "notes":           recipe.get("Notes", ""),
            "keywords":        recipe.get("Keywords", ""),
            "image":           image_url,
            "prep_time":       d.get("Prep Time", ""),
            "cook_time":       d.get("Cook Time", ""),
            "total_time":      d.get("Total Time", ""),
            "yield":           d.get("Yield", ""),
            "category":        d.get("Category", ""),
            "method":          d.get("Method", ""),
            "cuisine":         d.get("Cuisine", ""),
            "diet":            d.get("Diet", ""),
            "serving_size":    n.get("Serving Size", ""),
            "calories":        n.get("Calories", ""),
            "sugar":           n.get("Sugar", ""),
            "sodium":          n.get("Sodium", ""),
            "fat":             n.get("Fat", ""),
            "saturated_fat":   n.get("Saturated Fat", ""),
            "unsaturated_fat": n.get("Unsaturated Fat", ""),
            "trans_fat":       n.get("Trans Fat", ""),
            "carbohydrates":   n.get("Carbohydrates", ""),
            "fiber":           n.get("Fiber", ""),
            "protein":         n.get("Protein", ""),
            "cholesterol":     n.get("Cholesterol", ""),
        },
    }

    try:
        response = requests.post(
            f"{wp_url.rstrip('/')}/wp-json/wp/v2/tasty_recipe",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if response.status_code == 404:
            print("[recipe] Tasty Recipes plugin endpoint not found (404) — plugin may not be active")
            return None
        if response.status_code == 401:
            print("[recipe] WordPress auth failed (401) — check credentials")
            return None
        response.raise_for_status()

        recipe_id = response.json()["id"]
        shortcode = f'[tasty-recipe id="{recipe_id}"]'
        print(f"[recipe] Shortcode built ✅ — {shortcode}")
        return shortcode

    except requests.exceptions.ConnectionError:
        print(f"[recipe] Cannot reach WordPress at {wp_url}")
        return None
    except Exception as e:
        print(f"[recipe] Failed to create Tasty Recipe post: {e}")
        return None


# ── Step 3: Inject shortcode into article ────────────────────────────

def inject_into_content(shortcode: str, article_content: str) -> str:
    """
    Insert shortcode before the FAQ section.
    Falls back to appending at end if FAQ not found.
    """
    for marker in ("<h2>FAQ", "<h2>Frequently Asked Questions"):
        idx = article_content.find(marker)
        if idx != -1:
            result = article_content[:idx] + shortcode + "\n\n" + article_content[idx:]
            print("[recipe] Recipe card injected before FAQ ✅")
            return result

    print("[recipe] FAQ section not found — appending recipe card at end")
    return article_content + "\n\n" + shortcode
