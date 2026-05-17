"""
Prompt configuration for HTML static website recipe generation.

Scope: ONLY used by HtmlRecipeGenerator for html_static / html_recipe_site websites.
       WordPress prompts live exclusively in content_engine/article_generator.py.

Output contract: the LLM must return a single JSON object matching HTML_RECIPE_SCHEMA.
"""

# ---------------------------------------------------------------------------
# System prompt — structural contract sent as the "system" role.
# Never changes between requests. Keeps the user prompt focused on the task.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a strict JSON API for a recipe blog. "
    "Return only one valid JSON object. "
    "No markdown fences. No explanation. No text before or after the object."
)

# ---------------------------------------------------------------------------
# User prompt — injected with {keyword} and {available_categories_json}.
# Temperature 0.25 keeps schema compliance high while allowing natural prose.
# ---------------------------------------------------------------------------

USER_PROMPT = """\
Generate a complete, original recipe for a food blog.

Keyword: {keyword}
Available categories (pick one): {available_categories_json}

Return EXACTLY this JSON structure — no extra keys, no omissions:

{{
  "title": "Recipe title that naturally includes the keyword (55-70 characters)",
  "meta_description": "SEO meta description with keyword, 130-155 characters, written to drive clicks",
  "selected_category": {{
    "id": 0,
    "name": "Exact name from available categories",
    "slug": "category-slug"
  }},
  "description": "2-3 engaging sentences describing the dish, key flavors, and why readers will love it",
  "heroImagePrompt": "Detailed Midjourney prompt for the recipe hero photo: food styling, lighting, plating, angle, mood",
  "prepTime": "e.g. 15 min",
  "cookTime": "e.g. 25 min",
  "totalTime": "e.g. 40 min",
  "servings": "e.g. 4 servings",
  "rating": 4.7,
  "ratingCount": 142,
  "ingredients": [
    "1 cup all-purpose flour",
    "2 large eggs, beaten"
  ],
  "instructions": [
    "Preheat oven to 180°C (350°F) and line a baking tray with parchment paper.",
    "In a large bowl, whisk together the flour and eggs until smooth."
  ],
  "tags": ["easy", "quick", "healthy", "weeknight", "family-friendly"],
  "nutritionFacts": {{
    "calories": "320 kcal",
    "protein": "14 g",
    "carbs": "38 g",
    "fat": "12 g"
  }},
  "notes": [
    "Store leftovers in an airtight container in the fridge for up to 3 days.",
    "Substitute Greek yogurt for sour cream for a lighter version."
  ],
  "faq": [
    {{
      "question": "Can I make this ahead of time?",
      "answer": "Yes, you can prepare this up to 24 hours in advance and refrigerate until ready to serve."
    }}
  ]
}}

Rules (follow every one):
- title must include the keyword naturally — not forced
- selected_category must be the single best match from the available categories list; use id=0 if no categories are provided
- description must be specific to this recipe — no generic filler
- prepTime, cookTime, totalTime must be realistic for this specific recipe and consistent (prep + cook ≈ total)
- ingredients: minimum 6 items, each a complete line with quantity, unit, and ingredient name
- instructions: minimum 5 clear, actionable steps written in active voice; each step one logical action
- tags: 4-7 lowercase tags relevant to the recipe
- notes: 2-4 practical tips covering storage, substitutions, or variations
- faq: 2-3 genuine questions a home cook might ask, with clear helpful answers
- nutritionFacts: all four fields required, realistic values for one serving
- Forbidden ingredients: pork, bacon, ham, lard, alcohol, wine, beer, gelatin from pork
- Language: English

Return only the JSON object. No other text.
"""

# ---------------------------------------------------------------------------
# Schema reference (not sent to LLM — used by HtmlRecipeGenerator._validate)
# ---------------------------------------------------------------------------

HTML_RECIPE_SCHEMA = {
    "title": str,
    "meta_description": str,
    "selected_category": dict,
    "description": str,
    "heroImagePrompt": str,
    "prepTime": str,
    "cookTime": str,
    "totalTime": str,
    "servings": str,
    "rating": (int, float),
    "ratingCount": int,
    "ingredients": list,
    "instructions": list,
    "tags": list,
    "nutritionFacts": dict,
    "notes": list,
    "faq": list,
}

REQUIRED_NUTRITION_KEYS = ("calories", "protein", "carbs", "fat")
REQUIRED_CATEGORY_KEYS = ("name", "slug")
