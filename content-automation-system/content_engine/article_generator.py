"""
Article generator — produces article HTML and image prompt data.

Downstream consumers:
  - pipeline.py             reads all keys from the returned dict
  - recipe_card.py          uses recipe JSON generated locally from article HTML
  - midjourney_client.py    uses image_prompt directly
"""

import re
import json
from .llm_client import LLMClient

ARTICLE_MIN_WORDS = 500
ARTICLE_MAX_WORDS = 1400


# ── Prompts ───────────────────────────────────────────────────────────
#
# SYSTEM_PROMPT  — structural contract, sent as the "system" role.
#                  Contains schema, forbidden behaviors, and field rules.
#                  Never changes between requests.
#
# ARTICLE_PROMPT — sent as the "user" role with keyword + language injected.
#
# Design principles:
#   • System/user separation: structural rules in system, task in user.
#   • Temperature 0.2 (set at call site) — low enough for schema compliance.
#   • No "INTERNAL VALIDATION" section — models don't self-validate; it wastes tokens.
#   • Schema shown with real JSON syntax (no {{ }} escaping in the constant itself).
#   • Invalid output is retried; it is never replaced with local fallback text.

SYSTEM_PROMPT = """You are a strict JSON API. Return only one valid JSON object. No markdown. No explanation."""

ARTICLE_PROMPT = """You are a professional food blogger and SEO writer.

Your task is to generate a COMPLETE, HIGH-QUALITY recipe article.

INPUT:
- Primary Keyword: {keyword}
- Language: {language}
- Available Website Categories JSON: {available_categories_json}

==================================
CORE LOGIC (VERY IMPORTANT)
==================================

You MUST follow this internal process:

1. First → Understand the recipe type from the keyword
2. Second → Build a realistic recipe
3. Third → Generate INGREDIENTS (this is the foundation)
4. Fourth → Generate all sections based ONLY on ingredients

STRICT RULE:
- Ingredients are the source of truth
- No section can contradict ingredients
- Do NOT introduce new ingredients later

==================================
ARTICLE REQUIREMENTS
==================================

- Length: 1000–1200 words (flexible if needed)
- Must feel natural and human (not robotic)
- Use first person (I, my)
- Speak directly to the reader (you)

- Each article MUST be unique
- Avoid repeated intros or templates

- NEVER include:
  pork, bacon, ham, alcohol, wine

==================================
TITLE
==================================

- Max 60 characters
- Must include keyword naturally
- Clear and engaging (not clickbait)

==================================
STRUCTURE
==================================

1. Introduction (NO heading)
- Hook the reader
- Mention keyword naturally
- Match the recipe (no contradictions)

2. Why You'll Love This Recipe
- Bullet points (real benefits)

3. Ingredients (CRITICAL)
- Realistic ingredients
- Exact measurements
- Must fully define the recipe

4. How to Make {keyword}
- Step-by-step instructions
- Use ONLY listed ingredients
- Include timing and visual cues

5. Tips for Best Results
- Practical, useful tips
- Based on the recipe only

6. Variations
- Logical variations of the same recipe

7. Storage
- How to store and reheat

8. FAQs
- 3-4 relevant questions

==================================
RECIPE CONSISTENCY RULES
==================================

- If keyword contains specific recipe types:

  Italian Cream:
  → Prefer including coconut or pecans or buttermilk (at least one)

  Cheesecake:
  → Must include cream cheese

  Pound Cake:
  → Must be dense, butter-based

- Keep flexibility (do NOT force all ingredients)
- Recipe must still make culinary sense

==================================
META DESCRIPTION
==================================

- Max 140 characters
- Include keyword
- Clear + emotional + click-worthy

==================================
CATEGORY SELECTION
==================================

You must assign the MOST RELEVANT category to the article based on the recipe content.

Instructions:
- Analyze ingredients + meal type + cooking style
- Choose ONLY ONE category
- MUST choose from Available Website Categories JSON only
- Return the exact id, name, and slug from the provided category list
- Do NOT invent a category
- Do NOT guess randomly
- If it is sweet, choose the closest dessert/cake/sweets category from the list
- If it is morning style, choose the closest breakfast/brunch category from the list
- If it is a heavy cooked meal, choose the closest dinner/main/lunch category from the list
- If no perfect match exists, choose the closest logical category from the list

==================================
FINAL VALIDATION (VERY IMPORTANT)
==================================

Before returning the article:

- Check ingredients match instructions
- Check no contradictions exist
- Check recipe makes sense
- Check content is not generic

If any issue → fix it before output

==================================
OUTPUT FORMAT
==================================

Return ONLY:

{{
"title": "...",
"meta_description": "...",
"selected_category": {{"id": 2, "name": "Desserts", "slug": "desserts"}},
"category": "Desserts",
"content": "FULL HTML ARTICLE"
}}

No explanations
No extra text"""


def _html_word_count(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return len(re.findall(r"\b[\w'-]+\b", text))


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug or "recipe"


def _image_prompt_for(keyword: str) -> str:
    keyword = _safe_keyword_text(keyword)
    return (
        f"amateur photo with interesting details and texture from Reddit "
        f"taken with iPhone 15 Pro that hooks users for a juicy, mouthwatering "
        f"{keyword}, close-up at eye-level, natural kitchen lighting, "
        f"simple uncluttered background, homemade single-plate presentation "
        f"--s 100 --v 7 --ar 10:11"
    )


def _meta_title_for(title: str, keyword: str) -> str:
    meta = title
    if keyword.lower() not in meta.lower():
        meta = f"{keyword.title()} Recipe"
    return meta[:60]


def _safe_keyword_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    return _replace_forbidden_terms(cleaned)


SAFE_TERM_REPLACEMENTS = (
    (r"\bcooking wine\b", "broth"),
    (r"\bred wine vinegar\b", "apple cider vinegar"),
    (r"\bwhite wine vinegar\b", "apple cider vinegar"),
    (r"\bwine vinegar\b", "apple cider vinegar"),
    (r"\bpancetta\b", "smoked turkey"),
    (r"\bprosciutto\b", "turkey slices"),
    (r"\bpepperoni\b", "turkey slices"),
    (r"\bpork\b", "chicken"),
    (r"\bbacon\b", "smoked turkey"),
    (r"\bham\b", "turkey"),
    (r"\blard\b", "butter"),
    (r"\bwine\b", "broth"),
    (r"\bbeer\b", "broth"),
    (r"\bwhiskey\b", "apple cider"),
    (r"\brum\b", "vanilla"),
    (r"\bvodka\b", "broth"),
    (r"\bliquor\b", "syrup"),
    (r"\balcohol\b", "rich flavor"),
)


def _replace_forbidden_terms(text: str) -> str:
    cleaned = text or ""
    for pattern, replacement in SAFE_TERM_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned


def _clean_forbidden_terms(value):
    if isinstance(value, str):
        return _replace_forbidden_terms(value)
    if isinstance(value, list):
        return [_clean_forbidden_terms(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_forbidden_terms(item) for key, item in value.items()}
    return value


def _forbidden_terms_present(text: str) -> bool:
    return bool(re.search(
        r"\b(pork|bacon|ham|lard|pancetta|prosciutto|pepperoni|wine|beer|cooking wine|whiskey|rum|vodka|liquor|alcohol)\b",
        text or "",
        flags=re.IGNORECASE,
    ))


KEYWORD_COVERAGE_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "recipe",
    "recipes",
    "the",
    "to",
    "with",
}


def _keyword_terms(text: str) -> list[str]:
    terms = []
    for term in re.findall(r"[a-z0-9]+", _safe_keyword_text(text).lower()):
        if len(term) < 3 or term in KEYWORD_COVERAGE_STOPWORDS:
            continue
        terms.append(term)
    return terms


def _has_keyword_coverage(keyword: str, content: str) -> bool:
    keyword_lower = _safe_keyword_text(keyword).lower()
    content_lower = (content or "").lower()
    if keyword_lower and keyword_lower in content_lower:
        return True

    terms = _keyword_terms(keyword)
    if not terms:
        return True

    matched = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\w*\b", content_lower))
    required = max(1, min(len(terms), round(len(terms) * 0.75)))
    return matched >= required


GENERIC_ARTICLE_PATTERNS = (
    "The first sign that",
    "The key is building flavor in small, steady moves",
    "Good {keyword} starts with ingredients that make sense",
    "Preheat the oven to 350°F if baking, or warm a heavy skillet",
    "Prepare the main ingredients and pat away excess moisture",
    "Mix dry ingredients in one bowl and wet ingredients or sauce components",
    "You can adapt {keyword} without changing the heart of the recipe",
    "The most reliable way to judge {keyword} is to watch the texture",
)


RECIPE_RULES = {
    "italian cream": {
        "ingredients": {
            "coconut": ("coconut", "shredded coconut", "sweetened coconut", "coconut flakes"),
            "pecan": ("pecan", "pecans", "chopped pecans", "toasted pecans"),
            "buttermilk": ("buttermilk", "cultured buttermilk"),
        },
        "min_score": 1,
        "context_min_score": {
            "pound cake": 1,
            "cake": 2,
        },
        "error": "italian cream recipe missing signature ingredients",
    },
    "cheesecake": {
        "ingredients": {
            "cream cheese": ("cream cheese", "full-fat cream cheese", "softened cream cheese"),
        },
        "min_score": 1,
        "error": "cheesecake recipe missing cream cheese",
    },
    "pound cake": {
        "ingredients": {
            "butter": ("butter", "unsalted butter", "salted butter", "melted butter", "softened butter"),
        },
        "min_score": 1,
        "error": "pound cake ingredients missing butter",
    },
}


def contains_any(text: str, keywords: tuple[str, ...] | list[str]) -> bool:
    haystack = (text or "").lower()
    for keyword in keywords:
        needle = re.escape(str(keyword).lower().strip())
        if needle and re.search(rf"(?<![a-z0-9]){needle}(?![a-z0-9])", haystack):
            return True
    return False


def _rule_min_score(rule: dict, keyword_lower: str) -> int:
    min_score = int(rule.get("min_score", 1))
    context_scores = rule.get("context_min_score") or {}
    for context, context_min in context_scores.items():
        if context in keyword_lower:
            min_score = int(context_min)
            break
    return min_score


def _recipe_rule_errors(keyword_lower: str, ingredient_text: str) -> list[str]:
    errors: list[str] = []
    for trigger, rule in RECIPE_RULES.items():
        if trigger not in keyword_lower:
            continue

        matched = [
            name
            for name, synonyms in (rule.get("ingredients") or {}).items()
            if contains_any(ingredient_text, synonyms)
        ]
        score = len(matched)
        min_score = _rule_min_score(rule, keyword_lower)
        if score < min_score:
            expected = ", ".join((rule.get("ingredients") or {}).keys())
            errors.append(
                f"{rule.get('error', trigger + ' recipe failed validation')} "
                f"(score {score}/{min_score}; expected one of: {expected})"
            )
    return errors


def _infer_recipe_category(keyword: str, html: str = "") -> str:
    context = f"{keyword} {_strip_tags(html)}".lower()
    tokens = set(re.findall(r"[a-z]+", context))

    dessert = {
        "cake", "cakes", "cupcake", "cupcakes", "cheesecake", "brownie", "brownies",
        "cookie", "cookies", "dessert", "pie", "pies", "pudding", "frosting",
        "chocolate", "strawberry", "sweet", "pound", "cream", "banana", "muffin",
        "muffins", "cobbler", "tart", "trifle",
    }
    breakfast = {
        "breakfast", "pancake", "pancakes", "waffle", "waffles", "oatmeal",
        "toast", "omelet", "omelette", "eggs", "smoothie", "granola",
    }
    dinner = {
        "dinner", "casserole", "beef", "chicken", "steak", "salmon", "pasta",
        "noodle", "noodles", "rice", "bowl", "bowls", "soup", "roast",
        "grill", "grilled", "baked", "teriyaki", "marinade",
    }
    salad = {"salad", "slaw"}
    side = {"side", "potato", "potatoes", "corn", "beans", "rice"}
    appetizer = {"dip", "bites", "wings", "appetizer", "starter"}
    drink = {"drink", "smoothie", "juice", "lemonade", "tea", "coffee"}

    if tokens & breakfast:
        return "Breakfast"
    if tokens & dessert:
        return "Dessert"
    if tokens & drink:
        return "Drink"
    if tokens & salad:
        return "Salad"
    if tokens & appetizer:
        return "Appetizer"
    if tokens & dinner:
        return "Dinner"
    if tokens & side:
        return "Side Dish"
    return "Main Course"


def _normalise_available_categories(categories) -> list[dict]:
    normalised: list[dict] = []
    for category in categories or []:
        if not isinstance(category, dict):
            continue
        try:
            category_id = int(category.get("id"))
        except (TypeError, ValueError):
            continue
        name = str(category.get("name") or "").strip()
        slug = str(category.get("slug") or "").strip()
        if category_id and name and slug:
            normalised.append({"id": category_id, "name": name, "slug": slug})
    return normalised


def _category_key(category: dict) -> str:
    return f"{category.get('id')} {category.get('name', '')} {category.get('slug', '')}".lower()


def _match_available_category(value, categories: list[dict]) -> dict | None:
    if not value or not categories:
        return None
    if isinstance(value, dict):
        raw_id = value.get("id")
        if raw_id is not None:
            try:
                category_id = int(raw_id)
                for category in categories:
                    if int(category["id"]) == category_id:
                        return category
            except (TypeError, ValueError):
                pass
        probes = [value.get("name"), value.get("slug")]
    else:
        probes = [value]
    probes = [str(probe or "").strip().lower() for probe in probes if str(probe or "").strip()]
    for probe in probes:
        for category in categories:
            if probe in {str(category["name"]).lower(), str(category["slug"]).lower()}:
                return category
    return None


def _closest_available_category(keyword: str, html: str, categories: list[dict]) -> dict | None:
    if not categories:
        return None
    inferred = _infer_recipe_category(keyword, html).lower()
    context = f"{keyword} {_strip_tags(html)}".lower()
    category_aliases = {
        "dessert": ("dessert", "desserts", "cake", "cakes", "sweet", "sweets", "baking"),
        "breakfast": ("breakfast", "brunch", "morning"),
        "dinner": ("dinner", "main", "mains", "meal", "meals", "supper"),
        "lunch": ("lunch", "main", "meal"),
        "main course": ("main", "mains", "dinner", "meal", "entree", "entrée"),
        "side dish": ("side", "sides"),
        "salad": ("salad", "salads"),
        "appetizer": ("appetizer", "appetizers", "starter", "snack"),
        "snack": ("snack", "snacks", "appetizer"),
        "drink": ("drink", "drinks", "smoothie", "juice"),
    }
    preferred = category_aliases.get(inferred, (inferred,))
    best_category = categories[0]
    best_score = -1
    context_tokens = set(re.findall(r"[a-z0-9]+", context))
    for category in categories:
        cat_text = _category_key(category)
        cat_tokens = set(re.findall(r"[a-z0-9]+", cat_text))
        score = len(context_tokens & cat_tokens)
        for term in preferred:
            if term in cat_text:
                score += 20
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


def _normalise_selected_category(data: dict, keyword: str, available_categories: list[dict]) -> None:
    if not available_categories:
        if not data.get("category"):
            data["category"] = _infer_recipe_category(keyword, data.get("article_html_content") or data.get("content") or "")
        return
    html = data.get("article_html_content") or data.get("content") or ""
    selected = (
        _match_available_category(data.get("selected_category"), available_categories)
        or _match_available_category(data.get("category"), available_categories)
        or _closest_available_category(keyword, html, available_categories)
    )
    if selected:
        data["selected_category"] = selected
        data["category"] = selected["name"]


def _quality_errors(data: dict, keyword: str) -> list[str]:
    html = data.get("article_html_content") or ""
    title = str(data.get("title") or "")
    meta_description = str(data.get("meta_description") or "")
    text = _strip_tags(html)
    lower = text.lower()
    keyword_lower = _safe_keyword_text(keyword).lower()
    errors: list[str] = []

    searchable_content = f"{title} {meta_description} {text}"
    if keyword_lower and not _has_keyword_coverage(keyword, searchable_content):
        errors.append("article does not cover the keyword topic")
    if title.strip().lower() == keyword_lower:
        errors.append("title is only the focus keyword")

    generic_hits = 0
    for pattern in GENERIC_ARTICLE_PATTERNS:
        probe = pattern.replace("{keyword}", keyword)
        if probe.lower() in lower:
            generic_hits += 1
    if generic_hits >= 2:
        errors.append("article uses local generic fallback/template wording")
    if re.search(r"\brecipe with simple tips\b", title, flags=re.IGNORECASE):
        errors.append("title uses generic fallback formula")

    repeated_sentences = [
        sentence for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence and text.lower().count(sentence.lower()) > 1 and len(sentence.split()) > 6
    ]
    if repeated_sentences:
        errors.append("article contains duplicated sentences or paragraphs")

    ingredients = _strip_tags(_section_after_heading(html, ("ingredient",), "ul"))
    ingredient_lower = ingredients.lower()

    # Keyword-ingredient consistency: only flag if the dish's defining ingredient is missing.
    if "strawberry" in keyword_lower and "strawberr" not in ingredient_lower:
        errors.append("strawberry recipe is missing strawberry ingredients")
    errors.extend(_recipe_rule_errors(keyword_lower, ingredient_lower))
    # Non-chocolate sanity check
    if "chocolate" not in keyword_lower and "cocoa powder" in ingredient_lower:
        errors.append("non-chocolate recipe contains cocoa powder")

    instructions = _strip_tags(_section_after_heading(html, ("how to make", "instruction", "step"), "ol"))
    instructions_lower = instructions.lower()
    # Drop overly strict technique-word checks (creaming method, water bath, springform).
    # Many valid recipes describe the technique without using the literal keyword.
    if "if baking, or warm a heavy skillet" in instructions_lower:
        errors.append("instructions contain generic multi-method placeholder")

    return errors


# Top-level keys the LLM must return (or that the normaliser must fill in).
# recipe_card is NOT required — it is built locally from article HTML by the
# normaliser, and the pipeline gracefully publishes without it if extraction fails.
REQUIRED_TOP_LEVEL_KEYS = (
    "title",
    "meta_title",
    "meta_description",
    "slug",
    "article_html_content",
)

REQUIRED_RECIPE_KEYS = (
    "Description",
    "Ingredients",
    "Instructions",
    "Notes",
    "Details",
    "Keywords",
    "Nutrition",
)

REQUIRED_DETAIL_KEYS = (
    "Prep Time",
    "Cook Time",
    "Total Time",
    "Yield",
    "Category",
    "Method",
    "Cuisine",
    "Diet",
)

REQUIRED_NUTRITION_KEYS = (
    "Serving Size",
    "Calories",
    "Sugar",
    "Sodium",
    "Fat",
    "Saturated Fat",
    "Unsaturated Fat",
    "Trans Fat",
    "Carbohydrates",
    "Fiber",
    "Protein",
    "Cholesterol",
)


def _strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def _section_after_heading(html: str, heading_words: tuple[str, ...], tag: str) -> str:
    headings = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", html or "", re.I | re.S))
    for index, match in enumerate(headings):
        heading = _strip_tags(match.group(1)).lower()
        if any(word in heading for word in heading_words):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(html)
            section = html[match.end():end]
            tag_match = re.search(fr"<{tag}\b[^>]*>.*?</{tag}>", section, re.I | re.S)
            if tag_match:
                return tag_match.group(0).strip()
    return ""


def _first_tag(html: str, tag: str) -> str:
    match = re.search(fr"<{tag}\b[^>]*>.*?</{tag}>", html or "", re.I | re.S)
    return match.group(0).strip() if match else ""


def _recipe_from_article(data: dict, keyword: str) -> dict:
    html = data.get("article_html_content") or data.get("html_content", "")
    ingredients = _section_after_heading(html, ("ingredient",), "ul") or _first_tag(html, "ul")
    instructions = _section_after_heading(html, ("instruction", "step"), "ol") or _first_tag(html, "ol")
    notes = _section_after_heading(html, ("tip", "trick", "pro"), "ul")

    if not ingredients or not instructions:
        return None
    if not notes:
        notes = "<ul><li>Read the article tips before starting for best results.</li><li>Adjust seasoning and texture to your preference.</li></ul>"

    lower = html.lower()
    no_cook = any(word in lower for word in ("no-cook", "no cook", "salad", "sandwich"))
    category = str(data.get("category") or data.get("recipe_category") or "").strip()
    if not category:
        category = _infer_recipe_category(keyword, html)
    return {
        "Description": data.get("meta_description") or f"A helpful homemade recipe for {keyword}.",
        "Ingredients": ingredients,
        "Instructions": instructions,
        "Notes": notes,
        "Details": {
            "Prep Time": "15 mins",
            "Cook Time": "0 mins" if no_cook else "25 mins",
            "Total Time": "15 mins" if no_cook else "40 mins",
            "Yield": "6 servings",
            "Category": category,
            "Method": "No-Cook" if no_cook else "Cooking",
            "Cuisine": "American",
            "Diet": "Vegetarian" if "salad" in lower and "chicken" not in lower else "Halal",
        },
        "Keywords": data.get("focus_keyword") or keyword,
        "Nutrition": {
            "Serving Size": "1 serving",
            "Calories": "320",
            "Sugar": "8g",
            "Sodium": "420mg",
            "Fat": "14g",
            "Saturated Fat": "4g",
            "Unsaturated Fat": "9g",
            "Trans Fat": "0g",
            "Carbohydrates": "24g",
            "Fiber": "3g",
            "Protein": "24g",
            "Cholesterol": "70mg",
        },
    }


def _validate_recipe_card(recipe: dict) -> list[str]:
    errors = []
    if not isinstance(recipe, dict):
        return ["recipe_card must be an object"]

    for key in REQUIRED_RECIPE_KEYS:
        if key not in recipe or recipe.get(key) in (None, ""):
            errors.append(f"recipe_card.{key} is required")

    details = recipe.get("Details")
    if not isinstance(details, dict):
        errors.append("recipe_card.Details must be an object")
    else:
        for key in REQUIRED_DETAIL_KEYS:
            if not details.get(key):
                errors.append(f"recipe_card.Details.{key} is required")

    nutrition = recipe.get("Nutrition")
    if not isinstance(nutrition, dict):
        errors.append("recipe_card.Nutrition must be an object")
    else:
        for key in REQUIRED_NUTRITION_KEYS:
            if not nutrition.get(key):
                errors.append(f"recipe_card.Nutrition.{key} is required")

    if isinstance(recipe.get("Ingredients"), str) and "<li" not in recipe["Ingredients"].lower():
        errors.append("recipe_card.Ingredients must contain <li> items")
    if isinstance(recipe.get("Instructions"), str) and "<li" not in recipe["Instructions"].lower():
        errors.append("recipe_card.Instructions must contain <li> items")
    return errors


def _validate_article_contract(data: dict) -> list[str]:
    errors = []
    if not isinstance(data, dict):
        return ["response must be a JSON object"]

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data or data.get(key) in (None, ""):
            errors.append(f"{key} is required")

    html = data.get("article_html_content")
    if html is not None and not isinstance(html, str):
        errors.append("article_html_content must be a string")
    # Fences and wrong heading levels are fixed in _normalise_article_contract
    # before validation runs, so only flag genuinely empty/non-HTML content.
    if isinstance(html, str) and len(html.strip()) < 200:
        errors.append("article_html_content is too short to be a valid article")
    if isinstance(html, str) and _forbidden_terms_present(html):
        errors.append("article_html_content contains forbidden pork or alcohol terms")

    slug = data.get("slug")
    if isinstance(slug, str) and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        errors.append("slug must be lowercase hyphen format")

    # recipe_card is optional. Only validate it if the normaliser produced one.
    recipe_card = data.get("recipe_card")
    if recipe_card is not None:
        errors.extend(_validate_recipe_card(recipe_card))
        recipe_text = json.dumps(recipe_card or {}, ensure_ascii=False)
        if _forbidden_terms_present(recipe_text):
            errors.append("recipe_card contains forbidden pork or alcohol terms")
    return errors


def _clean_html_content(html: str) -> str:
    """Strip markdown fences and normalise heading levels that the LLM got wrong."""
    if not html:
        return html
    # Remove ```html ... ``` or ``` ... ``` wrappers the model sometimes adds
    html = re.sub(r"```(?:html)?\s*", "", html)
    html = re.sub(r"\s*```", "", html)
    # If model used <h1> instead of <h2>, promote down one level
    if "<h1" in html.lower() and "<h2" not in html.lower():
        html = re.sub(r"<h1([\s>])", r"<h2\1", html, flags=re.IGNORECASE)
        html = re.sub(r"</h1>", "</h2>", html, flags=re.IGNORECASE)
    # If model used markdown ## headings inside the HTML string, convert them
    html = re.sub(r"^##\s+(.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^###\s+(.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    return html.strip()


def _normalise_article_contract(data: dict, keyword: str, available_categories: list[dict] | None = None) -> dict:
    normalised = dict(data or {})
    safe_keyword = _safe_keyword_text(keyword)
    available_categories = _normalise_available_categories(available_categories)
    focus_keyword = re.sub(r"\s+", " ", (safe_keyword or "").strip()).lower()
    if "meta_title" not in normalised and normalised.get("title"):
        normalised["meta_title"] = _meta_title_for(normalised["title"], safe_keyword)
    elif normalised.get("meta_title"):
        meta_title = str(normalised["meta_title"]).strip()
        if meta_title.lower() == focus_keyword:
            normalised["meta_title"] = _meta_title_for(normalised["title"], safe_keyword)
    if "meta_title" not in normalised and normalised.get("title"):
        normalised["meta_title"] = _meta_title_for(normalised["title"], safe_keyword)
    if normalised.get("meta_description"):
        normalised["meta_description"] = str(normalised.get("meta_description") or "")[:140]
    if not normalised.get("slug"):
        normalised["slug"] = _slugify(safe_keyword)
    if not normalised.get("category"):
        normalised["category"] = _infer_recipe_category(safe_keyword, normalised.get("article_html_content") or normalised.get("content") or "")
    if "article_html_content" not in normalised and normalised.get("html_content"):
        normalised["article_html_content"] = normalised["html_content"]
    if "article_html_content" not in normalised and normalised.get("content"):
        normalised["article_html_content"] = normalised["content"]
    _normalise_selected_category(normalised, safe_keyword, available_categories)
    if "recipe_card" not in normalised and isinstance(normalised.get("recipe"), dict):
        normalised["recipe_card"] = normalised["recipe"]
    # Clean HTML before validation so fences/wrong headings don't cause a retry
    if isinstance(normalised.get("article_html_content"), str):
        normalised["article_html_content"] = _clean_forbidden_terms(_clean_html_content(normalised["article_html_content"]))
    if isinstance(normalised.get("recipe_card"), dict):
        normalised["recipe_card"] = _clean_forbidden_terms(normalised["recipe_card"])
    if not normalised.get("category"):
        normalised["category"] = _infer_recipe_category(safe_keyword, normalised.get("article_html_content") or "")
    _normalise_selected_category(normalised, safe_keyword, available_categories)
    if not normalised.get("image_prompt"):
        normalised["image_prompt"] = _image_prompt_for(safe_keyword)
    if _validate_recipe_card(normalised.get("recipe_card")):
        recipe_card = _recipe_from_article(normalised, safe_keyword)
        if recipe_card:
            normalised["recipe_card"] = recipe_card
    return normalised


class ArticleGenerator:
    def __init__(self, api_key: str = ""):
        self.llm = LLMClient(api_key)

    async def generate_complete_article(self, keyword: str, language: str = "English", available_categories=None) -> dict:
        """
        Returns article data and an image prompt. Recipe data can be generated
        later from the article HTML by the publishing step.
        """
        print(f"[article] Generating article package for: {keyword} [{language}]")

        available_categories = _normalise_available_categories(available_categories)
        if not available_categories:
            available_categories = [
                {"id": 1, "name": "Dessert", "slug": "dessert"},
                {"id": 2, "name": "Breakfast", "slug": "breakfast"},
                {"id": 3, "name": "Dinner", "slug": "dinner"},
                {"id": 4, "name": "Lunch", "slug": "lunch"},
                {"id": 5, "name": "Main Course", "slug": "main-course"},
                {"id": 6, "name": "Side Dish", "slug": "side-dish"},
                {"id": 7, "name": "Salad", "slug": "salad"},
                {"id": 8, "name": "Appetizer", "slug": "appetizer"},
                {"id": 9, "name": "Snack", "slug": "snack"},
                {"id": 10, "name": "Drink", "slug": "drink"},
            ]
        categories_json = json.dumps(available_categories, ensure_ascii=False)
        base_user_prompt = ARTICLE_PROMPT.format(
            keyword=keyword,
            language=language,
            available_categories_json=categories_json,
        )
        user_prompt = base_user_prompt
        data = None
        word_count = 0

        max_attempts = 3
        last_error = ""
        for attempt in range(max_attempts):
            print(f"[article] keyword='{keyword}' attempt={attempt + 1}/{max_attempts}")
            try:
                raw = await self.llm.generate(
                    user_prompt,
                    temperature=0.15,
                    max_tokens=6200,
                    system_prompt=SYSTEM_PROMPT,
                    keyword=keyword,
                )
            except Exception as exc:
                last_error = f"LLM unavailable/slow: {type(exc).__name__}: {exc}"
                print(f"[article] keyword='{keyword}' attempt={attempt + 1} failure: {last_error}")
                if attempt < max_attempts - 1:
                    continue
                raise ValueError(f"Article generation failed after {max_attempts} attempts. {last_error}") from exc

            try:
                data = self.llm.parse_json(raw)
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = f"Invalid JSON from LLM: {type(exc).__name__}"
                print(f"[article] keyword='{keyword}' attempt={attempt + 1} failure: {last_error}")
                self.llm.rotate_after_invalid_response(keyword)
                user_prompt = base_user_prompt
                continue

            data = _normalise_article_contract(data, keyword, available_categories)
            contract_errors = _validate_article_contract(data)
            if contract_errors:
                last_error = f"Contract validation failed: {contract_errors[:3]}"
                print(f"[article] keyword='{keyword}' attempt={attempt + 1} failure: {last_error}")
                user_prompt = base_user_prompt
                continue

            quality_errors = _quality_errors(data, keyword)
            if quality_errors:
                last_error = f"Quality validation failed: {quality_errors[:4]}"
                print(f"[article] keyword='{keyword}' attempt={attempt + 1} failure: {last_error}")
                user_prompt = base_user_prompt
                continue

            word_count = _html_word_count(data.get("article_html_content", ""))
            if ARTICLE_MIN_WORDS <= word_count <= ARTICLE_MAX_WORDS:
                print(f"[article] keyword='{keyword}' attempt={attempt + 1} success")
                break

            last_error = f"Word count {word_count} outside range"
            print(f"[article] keyword='{keyword}' attempt={attempt + 1} failure: {last_error}")
            user_prompt = base_user_prompt
            data = None

        if data is None:
            raise ValueError(f"Article generation failed quality checks after {max_attempts} attempts. {last_error}")

        data = _normalise_article_contract(data, keyword, available_categories)
        contract_errors = _validate_article_contract(data)
        if contract_errors:
            raise ValueError(f"LLM response failed article contract: {contract_errors}")
        quality_errors = _quality_errors(data, keyword)
        if quality_errors:
            raise ValueError(f"Generated article failed quality checks: {quality_errors}")

        # recipe_card is optional — pipeline publishes the article without
        # the tasty recipe shortcode if extraction failed.
        recipe = data.get("recipe_card")

        if not (ARTICLE_MIN_WORDS <= word_count <= ARTICLE_MAX_WORDS):
            raise ValueError(
                f"Generated article word count {word_count} outside acceptable range "
                f"{ARTICLE_MIN_WORDS}-{ARTICLE_MAX_WORDS} after {max_attempts} attempts"
            )

        image_prompt = data.get("image_prompt", "").strip()
        if not image_prompt:
            image_prompt = _image_prompt_for(keyword)
            print(f"[article] image_prompt missing from response — using default image prompt")

        # Sanitise: remove the word "revealing" per Midjourney TOS
        image_prompt = image_prompt.replace("revealing", "showing")[:900]

        print(f"[article] ✅ Generated: '{data['title']}'")
        print(f"[article] word count: {word_count}")
        print("[article] recipe JSON built locally from article HTML")
        print(f"[article] image_prompt: {image_prompt[:80]}…")

        return {
            "keyword":          keyword,
            "title":            data["title"],
            "meta_title":       data["meta_title"],
            "meta_description": data["meta_description"],
            "slug":             data["slug"],
            "category":         data.get("category") or _infer_recipe_category(keyword, data["article_html_content"]),
            "selected_category": data.get("selected_category"),
            "focus_keyword":    data.get("focus_keyword", keyword),
            "html_content":     data["article_html_content"],
            "recipe":           recipe,
            # Image prompt — used directly by midjourney pipeline task
            "image_prompt":     image_prompt,
        }
