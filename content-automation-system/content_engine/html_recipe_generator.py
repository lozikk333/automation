"""
HTML static recipe generator — produces structured JSON for website builder sites.

Scope: ONLY used for html_static / html_recipe_site websites.
       WordPress article generation is handled entirely by article_generator.py.

Output: validated dict matching HTML_RECIPE_SCHEMA in prompts/html_recipe_prompt.py.
        The dict is consumed by publishers/html_static.py for rendering and publishing.
"""

import json
import re
from typing import Any

from .llm_client import LLMClient
from .prompts.html_recipe_prompt import (
    HTML_RECIPE_SCHEMA,
    REQUIRED_CATEGORY_KEYS,
    REQUIRED_NUTRITION_KEYS,
    SYSTEM_PROMPT,
    USER_PROMPT,
)

# Maximum LLM attempts before raising. Each failed attempt rotates the API key.
_MAX_RETRIES = 3


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "recipe"


class HtmlRecipeValidationError(ValueError):
    """Raised when LLM output fails schema validation after all retries."""


class HtmlRecipeGenerator:
    """
    Generates structured recipe JSON for HTML static websites.

    Usage:
        gen = HtmlRecipeGenerator()
        recipe = asyncio.run(gen.generate_recipe(keyword, available_categories=[...]))
    """

    def __init__(self) -> None:
        self.llm = LLMClient()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self, data: Any) -> list[str]:
        """Return a list of validation error strings. Empty list means valid."""
        if not isinstance(data, dict):
            return ["Response is not a JSON object"]

        errors: list[str] = []

        # Top-level required fields and types
        for field, expected_type in HTML_RECIPE_SCHEMA.items():
            value = data.get(field)
            if value is None:
                errors.append(f"Missing field: {field}")
                continue
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    errors.append(f"{field} must be one of {expected_type}, got {type(value).__name__}")
            elif not isinstance(value, expected_type):
                errors.append(f"{field} must be {expected_type.__name__}, got {type(value).__name__}")

        if errors:
            # Don't run deeper checks if top-level types are wrong
            return errors

        # Non-empty strings
        for field in ("title", "meta_description", "description", "prepTime", "cookTime", "totalTime"):
            if not str(data.get(field, "")).strip():
                errors.append(f"{field} must not be empty")

        # Time fields must look like duration strings
        for field in ("prepTime", "cookTime", "totalTime"):
            val = str(data.get(field, ""))
            if not re.search(r"\d+\s*(min|hr|hour|sec)", val, re.IGNORECASE):
                errors.append(f"{field} must contain a duration (e.g. '15 min'), got: {val!r}")

        # Minimum list lengths
        if len(data.get("ingredients", [])) < 4:
            errors.append("ingredients must contain at least 4 items")
        if len(data.get("instructions", [])) < 3:
            errors.append("instructions must contain at least 3 steps")

        # All ingredients and instructions must be non-empty strings
        for i, item in enumerate(data.get("ingredients", [])):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"ingredients[{i}] must be a non-empty string")
        for i, step in enumerate(data.get("instructions", [])):
            if not isinstance(step, str) or not step.strip():
                errors.append(f"instructions[{i}] must be a non-empty string")

        # nutritionFacts
        nutrition = data.get("nutritionFacts", {})
        for key in REQUIRED_NUTRITION_KEYS:
            if not isinstance(nutrition.get(key), str) or not nutrition[key].strip():
                errors.append(f"nutritionFacts.{key} is missing or empty")

        # selected_category
        cat = data.get("selected_category", {})
        for key in REQUIRED_CATEGORY_KEYS:
            if not isinstance(cat.get(key), str) or not cat[key].strip():
                errors.append(f"selected_category.{key} is missing or empty")

        # faq
        faq = data.get("faq", [])
        if len(faq) < 1:
            errors.append("faq must contain at least 1 item")
        for i, item in enumerate(faq):
            if not isinstance(item, dict):
                errors.append(f"faq[{i}] must be an object")
                continue
            if not isinstance(item.get("question"), str) or not item["question"].strip():
                errors.append(f"faq[{i}].question is missing or empty")
            if not isinstance(item.get("answer"), str) or not item["answer"].strip():
                errors.append(f"faq[{i}].answer is missing or empty")

        return errors

    # ------------------------------------------------------------------
    # Normalization — fill defaults, fix slugs, match category ids
    # ------------------------------------------------------------------

    def _normalize(self, data: dict, keyword: str, available_categories: list) -> dict:
        # selected_category: ensure slug and match id from available list
        cat = data.get("selected_category") or {}
        if isinstance(cat, dict):
            if cat.get("name") and not cat.get("slug"):
                cat["slug"] = _slugify(cat["name"])
            if not cat.get("id"):
                cat["id"] = 0
                for ac in available_categories:
                    if isinstance(ac, dict) and (
                        ac.get("name", "").lower() == cat.get("name", "").lower()
                        or ac.get("slug", "") == cat.get("slug", "")
                    ):
                        cat["id"] = ac.get("id", 0)
                        break
        data["selected_category"] = cat

        # Numeric defaults
        if not isinstance(data.get("rating"), (int, float)):
            data["rating"] = 4.7
        if not isinstance(data.get("ratingCount"), int):
            data["ratingCount"] = 0

        # List defaults
        for field in ("tags", "notes"):
            if not isinstance(data.get(field), list):
                data[field] = []

        # servings default
        if not isinstance(data.get("servings"), str) or not data["servings"].strip():
            data["servings"] = "4 servings"

        # heroImagePrompt default (non-fatal if missing)
        if not isinstance(data.get("heroImagePrompt"), str):
            data["heroImagePrompt"] = (
                f"photorealistic homemade {data.get('title', keyword)}, "
                "appetizing food photography, close-up plated dish, natural kitchen light, "
                "rich texture, warm highlights, no text, no people --s 100 --v 7 --ar 16:9"
            )

        # Derived slug for URL generation
        data["slug"] = _slugify(data.get("title") or keyword)

        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_recipe(
        self,
        keyword: str,
        available_categories: list | None = None,
    ) -> dict:
        """
        Generate a validated, normalised recipe JSON dict.

        Retries up to _MAX_RETRIES times on validation failure, rotating
        the API key between attempts (matching LLMClient's existing pattern).

        Raises:
            HtmlRecipeValidationError  — schema invalid after all retries
            RuntimeError               — LLM network/API failure
        """
        available_categories = available_categories or []
        cats_json = json.dumps(available_categories, ensure_ascii=False)
        prompt = USER_PROMPT.format(
            keyword=keyword,
            available_categories_json=cats_json,
        )

        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                raw = await self.llm.generate(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.25,
                    max_tokens=3500,
                    keyword=keyword,
                )
            except Exception as exc:
                last_exc = exc
                print(
                    f"[html_recipe] Attempt {attempt}/{_MAX_RETRIES} — LLM call failed: "
                    f"{type(exc).__name__}: {exc}"
                )
                if attempt < _MAX_RETRIES:
                    continue
                raise RuntimeError(
                    f"HTML recipe generation failed after {_MAX_RETRIES} attempts: {last_exc}"
                ) from last_exc

            try:
                data = self.llm.parse_json(raw)
            except ValueError as exc:
                last_exc = exc
                print(
                    f"[html_recipe] Attempt {attempt}/{_MAX_RETRIES} — JSON parse failed: {exc}"
                )
                if attempt < _MAX_RETRIES:
                    self.llm.rotate_after_invalid_response(keyword)
                    continue
                raise HtmlRecipeValidationError(
                    f"HTML recipe JSON unparseable after {_MAX_RETRIES} attempts"
                ) from exc

            errors = self._validate(data)
            if errors:
                err_summary = "; ".join(errors[:5])  # show at most 5 errors in logs
                print(
                    f"[html_recipe] Attempt {attempt}/{_MAX_RETRIES} — "
                    f"validation failed ({len(errors)} error(s)): {err_summary}"
                )
                if attempt < _MAX_RETRIES:
                    self.llm.rotate_after_invalid_response(keyword)
                    continue
                raise HtmlRecipeValidationError(
                    f"Recipe JSON failed validation after {_MAX_RETRIES} attempts. "
                    f"Errors: {'; '.join(errors)}"
                )

            data = self._normalize(data, keyword, available_categories)
            print(
                f"[html_recipe] Generated: '{data['title']}' "
                f"(attempt {attempt}/{_MAX_RETRIES}, "
                f"category: {data['selected_category'].get('name', '—')})"
            )
            return data

        # Should never reach here, but satisfies type checker
        raise RuntimeError(f"HTML recipe generation exhausted all {_MAX_RETRIES} attempts")
