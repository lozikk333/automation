"""
Pinterest Pin Generation Service
=================================
Orchestrates the full flow:
  1. Receive top/bottom image URLs + article title
  2. Build pin via TemplateCompositor
  3. Return local JPG path (ready for upload)

Usage:
    from services.pin_generation_service import generate_pinterest_pin

    pin_path = generate_pinterest_pin(
        job_id           = 123,
        article_title    = "Best Chocolate Lava Cake",
        top_image_url    = "https://cdn.ttapi.io/...",
        bottom_image_url = "https://cdn.ttapi.io/...",
    )
"""

import os
from pathlib import Path
from compositor.template_compositor import TemplateCompositor
from services.pinterest_overlay_text import generate_overlay_text
from services.pin_template_registry import DEFAULT_TEMPLATE_ID


def generate_pinterest_pin(
    job_id: int,
    article_title: str,
    top_image_url: str,
    bottom_image_url: str,
    output_dir: str = "pins",
    output_path: str | None = None,
    template_id: str | None = None,
    template_style: dict | None = None,
) -> str | None:
    """
    Generate a 1000x1500px modern Pinterest pin JPG.

    Args:
        job_id:            Pipeline job ID (used for filename)
        article_title:     Article title displayed in the centre card
        top_image_url:     Midjourney U1 image URL (top section)
        bottom_image_url:  Midjourney U2 image URL (bottom section)
        output_dir:        Directory to save the JPG
        template_id:       Template JSON id from templates/pin_templates
        template_style:    Optional per-website style override.

    Returns:
        Local path to the JPG, or None on failure.
    """
    if not top_image_url or not bottom_image_url:
        print("[pin_service] Missing image URL(s) — skipping pin generation")
        return None

    output_path = output_path or os.path.join(output_dir, f"pin_job{job_id}.jpg")

    try:
        overlay_text, variations = generate_overlay_text(article_title)
        print(f"[pin_service] Overlay text: {overlay_text.replace(chr(10), ' | ')}")
        if len(variations) > 1:
            print("[pin_service] Overlay variations: " + " / ".join(v.replace("\n", " | ") for v in variations))

        compositor = TemplateCompositor(template_id or DEFAULT_TEMPLATE_ID, style_override=template_style)
        path = compositor.generate_pin(
            top_image_url    = top_image_url,
            bottom_image_url = bottom_image_url,
            title            = overlay_text,
            output_path      = output_path,
        )
        print(f"[pin_service] Pin ready: {path}")
        return path

    except Exception as e:
        print(f"[pin_service] Pin generation failed: {e}")
        return None
