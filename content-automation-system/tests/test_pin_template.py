"""
Test Pinterest pin template compositor.
Run: python tests/test_pin_template.py

Uses generated local images so the test can run without internet access.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from PIL import Image, ImageDraw
from services.pin_generation_service import generate_pinterest_pin

# ── Test config ───────────────────────────────────────────────────────
TITLE      = "Best Chocolate Lava Cake Recipe — Easy 25-Minute Dessert"


def sample_image_path(name: str, color: tuple[int, int, int]) -> str:
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    path = Path(f"data/cache/{name}.jpg")
    img = Image.new("RGB", (1400, 900), color)
    draw = ImageDraw.Draw(img)
    for offset in range(0, 1400, 28):
        draw.line((offset, 0, 1400 - offset // 3, 900), fill=((offset * 2) % 255, (offset * 3) % 255, (offset * 5) % 255), width=5)
    draw.rectangle((120, 120, 1280, 780), outline=(255, 255, 255), width=14)
    draw.text((180, 180), name, fill=(255, 255, 255))
    img.save(path, "JPEG", quality=92)
    return str(path)


def test_pin_generation():
    print("\n[1] Generating Pinterest pin...")
    path = generate_pinterest_pin(
        job_id           = 999,
        article_title    = TITLE,
        top_image_url    = sample_image_path("pin_template_top", (132, 74, 48)),
        bottom_image_url = sample_image_path("pin_template_bottom", (70, 112, 62)),
    )

    assert path is not None, "Pin generation returned None"
    assert os.path.exists(path), f"Output file not found: {path}"

    size_kb = os.path.getsize(path) / 1024
    print(f"  File   : {path}")
    print(f"  Size   : {size_kb:.0f} KB")
    assert 10 < size_kb < 2000, f"Unexpected file size: {size_kb:.0f} KB"

    from PIL import Image
    img = Image.open(path)
    assert img.size == (1000, 1500), f"Wrong dimensions: {img.size}"
    print(f"  Size   : {img.size[0]}×{img.size[1]}px ✅")
    print(f"\n  Open to inspect: open {path}")
    Path(path).unlink(missing_ok=True)
    Path("data/cache/pin_template_top.jpg").unlink(missing_ok=True)
    Path("data/cache/pin_template_bottom.jpg").unlink(missing_ok=True)
    print("\n✅ Pin template test passed!")


if __name__ == "__main__":
    test_pin_generation()
