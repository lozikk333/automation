"""
Pinterest pin template registry.

Templates are plain JSON files so new designs can be added without changing
the pipeline. The compositor validates and normalises the values it needs.
"""

from __future__ import annotations

import json
import copy
import re
from pathlib import Path
from typing import Any


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "pin_templates"
DEFAULT_TEMPLATE_ID = "u1_u2_white_band"
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class PinTemplateError(ValueError):
    pass


def _safe_template_id(template_id: str | None) -> str:
    template_id = (template_id or DEFAULT_TEMPLATE_ID).strip()
    if not re.fullmatch(r"[a-z0-9_-]+", template_id):
        raise PinTemplateError(f"Invalid pin template id: {template_id}")
    return template_id


def load_pin_template(template_id: str | None = None) -> dict[str, Any]:
    template_id = _safe_template_id(template_id)
    path = TEMPLATE_DIR / f"{template_id}.json"
    if not path.exists():
        if template_id != DEFAULT_TEMPLATE_ID:
            return load_pin_template(DEFAULT_TEMPLATE_ID)
        raise PinTemplateError(f"Default pin template is missing: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    data.setdefault("id", template_id)
    data.setdefault("label", template_id.replace("_", " ").title())
    return data


def _template_path(template_id: str | None) -> Path:
    template_id = _safe_template_id(template_id)
    return TEMPLATE_DIR / f"{template_id}.json"


def _require_hex_color(value: str, field: str) -> str:
    value = (value or "").strip()
    if not HEX_COLOR_RE.fullmatch(value):
        raise PinTemplateError(f"{field} must be a hex color like #ff585d")
    return value.lower()


def get_pin_template_style(template_id: str) -> dict[str, str]:
    data = load_pin_template(template_id)
    return extract_pin_template_style(data)


def extract_pin_template_style(data: dict[str, Any]) -> dict[str, str]:
    text_band = data.get("layout", {}).get("text_band", {})
    text_badge = data.get("layout", {}).get("text_badge", {})
    accent_text = data.get("layout", {}).get("accent_text", {})
    text = data.get("text", {})
    return {
        "id": data["id"],
        "label": data.get("label", data["id"]),
        "band_background": text_band.get("background", "#ff585d"),
        "band_border_color": text_band.get("border_color", "#ffffff"),
        "band_border_width": str(text_band.get("border_width", 0)),
        "band_radius": str(text_band.get("radius", 0)),
        "font_color": text.get("fill", "#ffffff"),
        "font_family": text.get("font_family", ""),
        "font_size_max": str(text.get("font_size_max", 92)),
        "font_size_min": str(text.get("font_size_min", 44)),
        "max_lines": str(text.get("max_lines", 2)),
        "max_words": str(text.get("max_words", 8)),
        "uppercase": bool(text.get("uppercase", True)),
        "stroke_fill": text.get("stroke_fill", "#111111"),
        "stroke_width": str(text.get("stroke_width", 0)),
        "shadow_fill": text.get("shadow_fill", "#111111"),
        "badge_enabled": bool(text_badge.get("enabled", False)),
        "badge_text": text_badge.get("text", ""),
        "badge_font_family": text_badge.get("font_family", text.get("font_family", "")),
        "badge_background": text_badge.get("background", "#ffffff"),
        "badge_fill": text_badge.get("fill", "#111111"),
        "badge_border_color": text_badge.get("border_color", "#111111"),
        "badge_font_size": str(text_badge.get("font_size", 34)),
        "badge_width": str(text_badge.get("width", 450)),
        "badge_height": str(text_badge.get("height", 56)),
        "badge_radius": str(text_badge.get("radius", 14)),
        "accent_enabled": bool(accent_text.get("enabled", False)),
        "accent_text": accent_text.get("text", ""),
        "accent_fill": accent_text.get("fill", "#ffd21a"),
        "accent_stroke_fill": accent_text.get("stroke_fill", "#111111"),
        "accent_font_size": str(accent_text.get("font_size", 116)),
    }


def apply_pin_template_style(data: dict[str, Any], style: dict[str, Any] | None) -> dict[str, Any]:
    if not style:
        return data

    data = copy.deepcopy(data)
    data.setdefault("layout", {}).setdefault("text_band", {})
    data.setdefault("layout", {}).setdefault("text_badge", {})
    data.setdefault("layout", {}).setdefault("accent_text", {})
    data.setdefault("text", {})

    def set_color(value: Any, target: tuple[str, ...], field: str) -> None:
        if value is None or value == "":
            return
        current = data
        for key in target[:-1]:
            current = current.setdefault(key, {})
        current[target[-1]] = _require_hex_color(str(value), field)

    def set_int(value: Any, target: tuple[str, ...], field: str, min_value: int, max_value: int) -> None:
        if value is None or value == "":
            return
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise PinTemplateError(f"{field} must be a number")
        parsed = max(min_value, min(max_value, parsed))
        current = data
        for key in target[:-1]:
            current = current.setdefault(key, {})
        current[target[-1]] = parsed

    set_color(style.get("band_background"), ("layout", "text_band", "background"), "band_background")
    set_color(style.get("font_color"), ("text", "fill"), "font_color")
    set_color(style.get("band_border_color"), ("layout", "text_band", "border_color"), "band_border_color")
    set_color(style.get("stroke_fill"), ("text", "stroke_fill"), "stroke_fill")
    set_color(style.get("shadow_fill"), ("text", "shadow_fill"), "shadow_fill")
    set_color(style.get("badge_background"), ("layout", "text_badge", "background"), "badge_background")
    set_color(style.get("badge_fill"), ("layout", "text_badge", "fill"), "badge_fill")
    set_color(style.get("badge_border_color"), ("layout", "text_badge", "border_color"), "badge_border_color")
    set_color(style.get("accent_fill"), ("layout", "accent_text", "fill"), "accent_fill")
    set_color(style.get("accent_stroke_fill"), ("layout", "accent_text", "stroke_fill"), "accent_stroke_fill")

    set_int(style.get("band_border_width"), ("layout", "text_band", "border_width"), "band_border_width", 0, 24)
    set_int(style.get("band_radius"), ("layout", "text_band", "radius"), "band_radius", 0, 120)
    set_int(style.get("font_size_max"), ("text", "font_size_max"), "font_size_max", 24, 180)
    set_int(style.get("font_size_min"), ("text", "font_size_min"), "font_size_min", 18, 120)
    set_int(style.get("max_lines"), ("text", "max_lines"), "max_lines", 1, 4)
    set_int(style.get("max_words"), ("text", "max_words"), "max_words", 1, 16)
    set_int(style.get("stroke_width"), ("text", "stroke_width"), "stroke_width", 0, 12)
    set_int(style.get("badge_font_size"), ("layout", "text_badge", "font_size"), "badge_font_size", 12, 90)
    set_int(style.get("badge_width"), ("layout", "text_badge", "width"), "badge_width", 80, 900)
    set_int(style.get("badge_height"), ("layout", "text_badge", "height"), "badge_height", 24, 140)
    set_int(style.get("badge_radius"), ("layout", "text_badge", "radius"), "badge_radius", 0, 80)
    set_int(style.get("accent_font_size"), ("layout", "accent_text", "font_size"), "accent_font_size", 24, 220)

    if style.get("font_family") is not None:
        data["text"]["font_family"] = str(style["font_family"]).strip()
    if style.get("uppercase") is not None:
        data["text"]["uppercase"] = bool(style["uppercase"])
    if style.get("badge_enabled") is not None:
        data["layout"]["text_badge"]["enabled"] = bool(style["badge_enabled"])
    if style.get("badge_text") is not None:
        data["layout"]["text_badge"]["text"] = str(style["badge_text"])[:40]
    if style.get("badge_font_family") is not None:
        data["layout"]["text_badge"]["font_family"] = str(style["badge_font_family"]).strip()
    if style.get("accent_enabled") is not None:
        data["layout"]["accent_text"]["enabled"] = bool(style["accent_enabled"])
    if style.get("accent_text") is not None:
        data["layout"]["accent_text"]["text"] = str(style["accent_text"])[:40]

    return data


def update_pin_template_style(
    template_id: str,
    *,
    band_background: str | None = None,
    font_color: str | None = None,
    **fields: Any,
) -> dict[str, str]:
    template_id = _safe_template_id(template_id)
    path = _template_path(template_id)
    if not path.exists():
        raise PinTemplateError(f"Pin template not found: {template_id}")

    data = load_pin_template(template_id)
    data.setdefault("layout", {}).setdefault("text_band", {})
    data.setdefault("layout", {}).setdefault("text_badge", {})
    data.setdefault("layout", {}).setdefault("accent_text", {})
    data.setdefault("text", {})

    if band_background is not None:
        data["layout"]["text_band"]["background"] = _require_hex_color(band_background, "band_background")
    if font_color is not None:
        data["text"]["fill"] = _require_hex_color(font_color, "font_color")

    color_targets = {
        "band_border_color": ("layout", "text_band", "border_color"),
        "stroke_fill": ("text", "stroke_fill"),
        "shadow_fill": ("text", "shadow_fill"),
        "badge_background": ("layout", "text_badge", "background"),
        "badge_fill": ("layout", "text_badge", "fill"),
        "badge_border_color": ("layout", "text_badge", "border_color"),
        "accent_fill": ("layout", "accent_text", "fill"),
        "accent_stroke_fill": ("layout", "accent_text", "stroke_fill"),
    }
    int_targets = {
        "band_border_width": ("layout", "text_band", "border_width", 0, 24),
        "band_radius": ("layout", "text_band", "radius", 0, 120),
        "font_size_max": ("text", "font_size_max", 24, 180),
        "font_size_min": ("text", "font_size_min", 18, 120),
        "max_lines": ("text", "max_lines", 1, 4),
        "max_words": ("text", "max_words", 1, 16),
        "stroke_width": ("text", "stroke_width", 0, 12),
        "badge_font_size": ("layout", "text_badge", "font_size", 12, 90),
        "badge_width": ("layout", "text_badge", "width", 80, 900),
        "badge_height": ("layout", "text_badge", "height", 24, 140),
        "badge_radius": ("layout", "text_badge", "radius", 0, 80),
        "accent_font_size": ("layout", "accent_text", "font_size", 24, 220),
    }

    for field, target in color_targets.items():
        value = fields.get(field)
        if value is not None:
            if len(target) == 2:
                data[target[0]][target[1]] = _require_hex_color(value, field)
            else:
                data[target[0]][target[1]][target[2]] = _require_hex_color(value, field)

    for field, target in int_targets.items():
        value = fields.get(field)
        if value is None or value == "":
            continue
        section, key, min_value, max_value = target[0], target[1], target[2], target[3]
        subkey = None
        if len(target) == 5:
            section, key, subkey, min_value, max_value = target
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise PinTemplateError(f"{field} must be a number")
        parsed = max(min_value, min(max_value, parsed))
        if subkey:
            data[section][key][subkey] = parsed
        else:
            data[section][key] = parsed

    if fields.get("font_family") is not None:
        data["text"]["font_family"] = str(fields["font_family"]).strip()
    if fields.get("uppercase") is not None:
        data["text"]["uppercase"] = bool(fields["uppercase"])
    if fields.get("badge_enabled") is not None:
        data["layout"]["text_badge"]["enabled"] = bool(fields["badge_enabled"])
    if fields.get("badge_text") is not None:
        data["layout"]["text_badge"]["text"] = str(fields["badge_text"])[:40]
    if fields.get("badge_font_family") is not None:
        data["layout"]["text_badge"]["font_family"] = str(fields["badge_font_family"]).strip()
    if fields.get("accent_enabled") is not None:
        data["layout"]["accent_text"]["enabled"] = bool(fields["accent_enabled"])
    if fields.get("accent_text") is not None:
        data["layout"]["accent_text"]["text"] = str(fields["accent_text"])[:40]

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return get_pin_template_style(template_id)


def list_pin_templates() -> list[dict[str, str]]:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    templates: list[dict[str, str]] = []
    for path in sorted(TEMPLATE_DIR.glob("*.json")):
        try:
            data = load_pin_template(path.stem)
        except Exception:
            continue
        templates.append({
            "id": data["id"],
            "label": data.get("label") or data["id"],
            "description": data.get("description", ""),
        })
    return templates
