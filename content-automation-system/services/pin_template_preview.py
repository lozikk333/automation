from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from compositor.template_compositor import TemplateCompositor


PREVIEW_TITLE = "Teriyaki Chicken Bowls"


def _draw_sample_food(path: Path, variant: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return str(path)

    img = Image.new("RGB", (1400, 900), (92, 68, 48))
    draw = ImageDraw.Draw(img)

    # Warm bowl background.
    draw.ellipse((-80, -160, 1480, 1100), fill=(205, 194, 174))
    draw.ellipse((90, 40, 1310, 860), fill=(94, 58, 42))
    draw.ellipse((140, 80, 1260, 815), fill=(68, 40, 30))

    if variant == "top":
        rice_box = (575, 90, 980, 430)
        protein_box = (170, 300, 940, 785)
        green_box = (960, 145, 1275, 520)
    else:
        rice_box = (150, 80, 560, 430)
        protein_box = (520, 240, 1235, 800)
        green_box = (885, 70, 1255, 360)

    # Rice.
    draw.ellipse(rice_box, fill=(246, 243, 232))
    for x in range(rice_box[0] + 25, rice_box[2] - 25, 28):
        for y in range(rice_box[1] + 18, rice_box[3] - 18, 30):
            draw.ellipse((x, y, x + 18, y + 10), fill=(232, 229, 215))

    # Saucy chicken.
    draw.ellipse(protein_box, fill=(126, 55, 25))
    draw.ellipse((protein_box[0] + 35, protein_box[1] + 30, protein_box[2] - 20, protein_box[3] - 40), fill=(158, 76, 31))
    for i in range(18):
        x = protein_box[0] + 40 + (i * 43) % (protein_box[2] - protein_box[0] - 100)
        y = protein_box[1] + 45 + (i * 61) % (protein_box[3] - protein_box[1] - 120)
        draw.rounded_rectangle((x, y, x + 150, y + 34), radius=18, fill=(111, 45, 21))
        draw.line((x + 12, y + 14, x + 138, y + 20), fill=(223, 132, 52), width=4)

    # Broccoli.
    for i in range(18):
        x = green_box[0] + (i * 41) % max(1, green_box[2] - green_box[0] - 70)
        y = green_box[1] + (i * 53) % max(1, green_box[3] - green_box[1] - 70)
        draw.ellipse((x, y, x + 82, y + 72), fill=(38, 120, 44))
        draw.ellipse((x + 14, y + 8, x + 66, y + 56), fill=(65, 153, 54))

    # Sesame and scallions.
    for i in range(90):
        x = 160 + (i * 97) % 1080
        y = 120 + (i * 59) % 670
        color = (239, 224, 183) if i % 3 else (75, 174, 70)
        draw.ellipse((x, y, x + 12, y + 7), fill=color)

    img = img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=115, threshold=3))
    img.save(path, "JPEG", quality=92)
    return str(path)


def _template_mtime(template_id: str) -> float:
    template_path = Path("templates/pin_templates") / f"{template_id}.json"
    font_path = Path("templates/fonts/LilitaOne-Regular.ttf")
    mtimes = [template_path.stat().st_mtime if template_path.exists() else 0]
    if font_path.exists():
        mtimes.append(font_path.stat().st_mtime)
    return max(mtimes)


def generate_template_preview(
    template_id: str,
    output_dir: str = "pins/previews",
    force: bool = False,
    style_override: dict | None = None,
    cache_key: str | None = None,
) -> str:
    preview_name = cache_key or template_id
    output_path = Path(output_dir) / f"{preview_name}.jpg"
    meta_path = Path(output_dir) / f"{preview_name}.json"
    top_path = Path("data/cache/pin_preview_top.jpg")
    bottom_path = Path("data/cache/pin_preview_bottom.jpg")

    template_mtime = _template_mtime(template_id)
    style_fingerprint = json.dumps(style_override or {}, sort_keys=True)
    if not force and output_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            if float(meta.get("template_mtime", 0)) >= template_mtime and meta.get("style") == style_fingerprint:
                return str(output_path)
        except Exception:
            pass

    top = _draw_sample_food(top_path, "top")
    bottom = _draw_sample_food(bottom_path, "bottom")

    compositor = TemplateCompositor(template_id, style_override=style_override)
    path = compositor.generate_pin(
        top_image_url=top,
        bottom_image_url=bottom,
        title=PREVIEW_TITLE,
        output_path=str(output_path),
    )
    meta_path.write_text(json.dumps({"template_id": template_id, "template_mtime": template_mtime, "style": style_fingerprint}), encoding="utf-8")
    return path
