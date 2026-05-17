import asyncio
import json
import os
import re

from content_engine.llm_client import LLMClient


OVERLAY_TEXT_PROMPT = """\
You are designing text overlay for a Pinterest pin image.

Your goal is to ensure the FULL title is always visible and fits perfectly inside the image.

INPUT:
- Full Title: {title}

RULES:

1. TEXT FITTING (CRITICAL)
- The full title MUST always be visible (no cutting, no overflow)
- Automatically choose shorter lines if the text is too long
- Never allow text to go outside boundaries

2. LINE BREAKING
- If the title is long:
  - Split into 2 or 3 balanced lines
  - Keep lines visually clean and centered
- Avoid awkward breaks (do not split words randomly)

3. FONT SIZE LOGIC
- Short title -> large font
- Medium title -> medium font
- Long title -> small font

4. MAX WIDTH CONTROL
- Text must stay inside safe margins
- Do not stretch text edge-to-edge

5. FALLBACK
- If the title is extremely long:
  - Shorten it intelligently while keeping meaning
  - Example:
    "Classic Chocolate Cake Recipe - Moist & Decadent"
    -> "Moist Chocolate Cake"
    -> or "Best Moist Chocolate Cake"

6. STYLE
- Bold, readable, high contrast
- Optimized for mobile view
- Clean spacing between lines

OUTPUT:
Return ONLY one valid JSON object:
{{
  "formatted_text_lines": ["LINE 1", "LINE 2"],
  "suggested_font_size": "large"
}}

The array must contain 2 or 3 strings.
suggested_font_size must be one of: large, medium, small.
"""


FONT_SIZE_BY_WORDS = ((5, "large"), (8, "medium"), (999, "small"))


def _clean_words(text: str) -> list[str]:
    text = re.sub(r"\b(pork|bacon|ham|lard|wine|beer|alcohol)\b", " ", text, flags=re.I)
    text = re.sub(r"[^A-Za-z0-9 '&-]+", " ", text)
    return [word for word in text.upper().split() if re.search(r"[A-Z0-9]", word)]


def _font_size_label(word_count: int) -> str:
    for max_words, label in FONT_SIZE_BY_WORDS:
        if word_count <= max_words:
            return label
    return "small"


def _balanced_lines(words: list[str], line_count: int) -> list[str]:
    if not words:
        return ["RECIPE"]
    line_count = max(1, min(line_count, len(words)))
    target = max(1, round(len(words) / line_count))
    lines = []
    cursor = 0
    for index in range(line_count):
        remaining_lines = line_count - index
        remaining_words = len(words) - cursor
        take = max(1, round(remaining_words / remaining_lines))
        if index == 0 and len(words) % line_count == 1 and take > 1:
            take -= 1
        lines.append(" ".join(words[cursor:cursor + take]))
        cursor += take
    return [line for line in lines if line]


def _shorten_extreme_title(words: list[str]) -> list[str]:
    drop_words = {"WITH", "AND", "THE", "A", "AN", "RECIPE", "HOMEMADE", "CLASSIC", "SIMPLE", "TIPS"}
    keep = [word for word in words if word not in drop_words]
    if len(keep) >= 3:
        return keep[:6]
    return words[:6]


def _fallback_overlay_result(article_title: str) -> dict:
    words = _clean_words(article_title)
    if len(words) > 10:
        words = _shorten_extreme_title(words)
    line_count = 2 if len(words) <= 6 else 3
    return {
        "formatted_text_lines": _balanced_lines(words, line_count),
        "suggested_font_size": _font_size_label(len(words)),
    }


def _parse_overlay_result(raw: str) -> dict | None:
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", (raw or "").strip())
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        return None

    lines = data.get("formatted_text_lines")
    if not isinstance(lines, list):
        return None
    clean_lines = []
    for line in lines:
        words = _clean_words(str(line))
        if words:
            clean_lines.append(" ".join(words))
    if not (2 <= len(clean_lines) <= 3):
        return None
    label = str(data.get("suggested_font_size") or "medium").lower()
    if label not in {"large", "medium", "small"}:
        label = _font_size_label(sum(len(line.split()) for line in clean_lines))
    return {"formatted_text_lines": clean_lines, "suggested_font_size": label}


def generate_overlay_text(article_title: str) -> tuple[str, list[str]]:
    """
    Return explicit overlay lines joined by newlines plus metadata strings.
    Falls back quickly when the LLM is unavailable so pin generation never blocks.
    """
    fallback = _fallback_overlay_result(article_title)
    prompt = OVERLAY_TEXT_PROMPT.format(title=article_title)
    try:
        llm = LLMClient(os.getenv("NVIDIA_API_KEY", ""))
        raw = asyncio.run(llm.generate(prompt, temperature=0.15, max_tokens=260))
        result = _parse_overlay_result(raw)
        if result:
            text = "\n".join(result["formatted_text_lines"])
            return text, [f"font_size={result['suggested_font_size']}"]
    except Exception as exc:
        print(f"[pin_text] LLM overlay text failed ({type(exc).__name__}): {exc}")
    text = "\n".join(fallback["formatted_text_lines"])
    return text, [f"font_size={fallback['suggested_font_size']}"]
