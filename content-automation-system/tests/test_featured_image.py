import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compositor.featured_image_handler import FeaturedImageHandler
from pathlib import Path
from PIL import Image, ImageDraw


def make_test_image() -> str:
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    path = Path("data/cache/test_featured_source.jpg")
    img = Image.new("RGB", (1800, 1200), (92, 57, 42))
    draw = ImageDraw.Draw(img)
    draw.ellipse((250, 120, 1550, 1080), fill=(145, 89, 54), outline=(245, 232, 210), width=18)
    draw.text((720, 540), "Local test image", fill=(255, 255, 255))
    img.save(path, "JPEG", quality=92)
    return str(path)


def test_featured_image():
    handler = FeaturedImageHandler

    # Download and prepare
    output_path = handler.download_and_prepare(
        url=make_test_image(),
        job_id=999,
        slug="chocolate-lava-cake",
        cache_dir="data/cache",
    )

    # Check file exists
    assert os.path.exists(output_path), f"Output file not found: {output_path}"
    print(f"File created: {output_path}")

    # Check dimensions
    info = handler.get_image_info(output_path)
    print(f"Dimensions: {info['width']}×{info['height']}, Size: {info['size_kb']} KB")

    assert info["width"] == 1200, f"Expected width 1200, got {info['width']}"
    assert info["height"] == 800, f"Expected height 800, got {info['height']}"
    assert info["size_kb"] <= 300, f"File too large: {info['size_kb']} KB"
    print("✅ Dimensions and file size OK")

    # Cleanup
    handler.cleanup(output_path)
    assert not os.path.exists(output_path), "Cleanup failed"
    handler.cleanup("data/cache/test_featured_source.jpg")
    print("✅ Cleanup OK")

    print("\n✅ FeaturedImageHandler all checks passed!")


if __name__ == "__main__":
    test_featured_image()
