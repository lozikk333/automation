"""
Tests for PinterestPinGenerator.
Run:
    source venv/bin/activate
    python tests/test_pinterest_pin.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from PIL import Image, ImageDraw
from compositor.pinterest_pin_generator import PinterestPinGenerator


def sample_image_path(index: int) -> str:
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    path = Path(f"data/cache/test_source_{index}.jpg")
    img = Image.new("RGB", (1200, 800), (70 + index * 17 % 120, 90 + index * 23 % 120, 120 + index * 29 % 100))
    draw = ImageDraw.Draw(img)
    draw.rectangle((80, 80, 1120, 720), outline=(255, 255, 255), width=12)
    for offset in range(0, 1200, 24):
        color = ((offset + index * 31) % 255, (offset * 2 + index * 17) % 255, (offset * 3 + index * 11) % 255)
        draw.line((offset, 0, 1200 - offset // 2, 800), fill=color, width=5)
    for y in range(40, 800, 90):
        draw.ellipse((100 + (y * index) % 500, y, 360 + (y * index) % 500, y + 70), fill=(255, 255, 255), outline=(30, 50, 70), width=3)
    draw.text((120, 120), f"Source {index}", fill=(255, 255, 255))
    img.save(path, "JPEG", quality=92)
    return str(path)


def test_dimensions_and_file():
    print("\n[1] Single pin — dimensions & file size")
    gen = PinterestPinGenerator()

    path = gen.generate_pin(
        top_image_url=sample_image_path(1),
        bottom_image_url=sample_image_path(2),
        title="Best Chocolate Lava Cake Recipe",
        output_path="data/cache/test_pin_basic.png",
    )

    assert Path(path).exists(), "File not created"

    img = Image.open(path)
    assert img.size == (1000, 1500), f"Wrong size: {img.size}"
    print(f"  Dimensions: {img.size} ✅")

    size_kb = Path(path).stat().st_size / 1024
    assert size_kb > 50, f"File suspiciously small: {size_kb:.0f} KB"
    print(f"  File size:  {size_kb:.0f} KB ✅")

    Path(path).unlink()
    print("  Cleanup ✅")


def test_long_title_wraps():
    print("\n[2] Long title auto-wrap")
    gen  = PinterestPinGenerator()
    long = "Easy Holiday Chocolate Desserts That Will Impress Your Guests: 10 Showstopping Recipes You Can Make In 30 Minutes"

    path = gen.generate_pin(
        top_image_url=sample_image_path(3),
        bottom_image_url=sample_image_path(4),
        title=long,
        output_path="data/cache/test_pin_long.png",
    )

    assert Path(path).exists()
    img = Image.open(path)
    assert img.size == (1000, 1500)
    print(f"  Long title handled, size {img.size} ✅")
    Path(path).unlink()


def test_auto_output_path():
    print("\n[3] Auto-generated output path")
    gen  = PinterestPinGenerator()
    path = gen.generate_pin(
        top_image_url=sample_image_path(5),
        bottom_image_url=sample_image_path(6),
        title="Auto Path Test",
    )

    assert path.startswith("pins/"), f"Expected pins/ prefix, got: {path}"
    assert Path(path).exists()
    print(f"  Saved to: {path} ✅")
    Path(path).unlink()


def test_batch_three_pins():
    print("\n[4] Batch — 3 pins")
    gen = PinterestPinGenerator()
    recipes = [
        "Rich Dark Chocolate Brownies Recipe",
        "Fluffy Chocolate Pancakes — Weekend Treat",
        "No-Bake Chocolate Cheesecake in 15 Minutes",
    ]

    paths = []
    for i, title in enumerate(recipes):
        path = gen.generate_pin(
            top_image_url=sample_image_path(10 + i),
            bottom_image_url=sample_image_path(20 + i),
            title=title,
            output_path=f"data/cache/test_batch_{i}.png",
        )
        paths.append(path)

    assert len(paths) == 3
    for p in paths:
        assert Path(p).exists()
        Path(p).unlink()

    print(f"  {len(paths)} pins generated and verified ✅")


if __name__ == "__main__":
    test_dimensions_and_file()
    test_long_title_wraps()
    test_auto_output_path()
    test_batch_three_pins()
    for p in Path("data/cache").glob("test_source_*.jpg"):
        p.unlink()
    print("\n🎉 All Pinterest pin tests passed!")
