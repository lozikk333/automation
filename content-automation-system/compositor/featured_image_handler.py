import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, unquote


class FeaturedImageHandler:
    # WordPress recommended featured image size
    TARGET_WIDTH = 1200
    TARGET_HEIGHT = 800
    MAX_FILE_SIZE_KB = 300

    @staticmethod
    def _load_image(url: str) -> Image.Image:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return Image.open(unquote(parsed.path)).convert("RGB")
        if not parsed.scheme and Path(url).exists():
            return Image.open(url).convert("RGB")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")

    @staticmethod
    def save_asset(url: str, output_path: str, max_width: int = 1600) -> str:
        """
        Save a Midjourney output as a local JPEG asset without changing its
        composition. Used for the one-generation multi-use image workflow.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img = FeaturedImageHandler._load_image(url)
        if max_width and img.width > max_width:
            new_h = int(img.height * (max_width / img.width))
            img = img.resize((max_width, new_h), Image.Resampling.LANCZOS)
        FeaturedImageHandler._save_optimised(img, output_path)
        size_kb = Path(output_path).stat().st_size / 1024
        print(f"Saved image asset: {output_path} ({size_kb:.0f} KB, {img.width}x{img.height})")
        return output_path

    @staticmethod
    def download_and_prepare(url: str, job_id: int, slug: str, cache_dir: str = "data/cache") -> str:
        """
        Download hero image from URL, resize to WordPress featured image
        dimensions, optimise file size, and save to local cache.

        Returns the local file path.
        """
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        print(f"Downloading hero image: {url}")
        img = FeaturedImageHandler._load_image(url)

        # Centre-crop to 3:2 aspect ratio (1200×800)
        img = FeaturedImageHandler._centre_crop(
            img,
            FeaturedImageHandler.TARGET_WIDTH,
            FeaturedImageHandler.TARGET_HEIGHT,
        )

        # Save with progressive compression, targeting ≤300 KB
        output_path = f"{cache_dir}/{job_id}_{slug}-hero.jpg"
        FeaturedImageHandler._save_optimised(img, output_path)

        size_kb = Path(output_path).stat().st_size / 1024
        print(f"Saved hero image: {output_path} ({size_kb:.0f} KB, {img.width}×{img.height})")
        return output_path

    @staticmethod
    def _centre_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        target_ratio = target_w / target_h
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            # wider than target — scale by height then crop width
            new_h = target_h
            new_w = int(img.width * (target_h / img.height))
        else:
            # taller than target — scale by width then crop height
            new_w = target_w
            new_h = int(img.height * (target_w / img.width))

        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return img.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def _save_optimised(img: Image.Image, path: str):
        """Save JPEG, stepping down quality until file is ≤ MAX_FILE_SIZE_KB."""
        for quality in (90, 80, 70, 60):
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
            size_kb = buffer.tell() / 1024
            if size_kb <= FeaturedImageHandler.MAX_FILE_SIZE_KB or quality == 60:
                with open(path, "wb") as f:
                    f.write(buffer.getvalue())
                return

    @staticmethod
    def get_image_info(file_path: str) -> dict:
        img = Image.open(file_path)
        size_kb = Path(file_path).stat().st_size / 1024
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format or Path(file_path).suffix.lstrip(".").upper(),
            "size_kb": round(size_kb, 1),
        }

    @staticmethod
    def cleanup(file_path: str):
        """Delete cached file after it has been uploaded to WordPress."""
        p = Path(file_path)
        if p.exists():
            p.unlink()
            print(f"Cleaned up cache: {file_path}")
