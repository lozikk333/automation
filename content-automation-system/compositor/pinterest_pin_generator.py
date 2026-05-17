"""
Dynamic Pinterest Pin Generator
================================
Generates 1000x1500px Pinterest pins with:
  - Top image     (60% = 900px) — hero, biggest visual impact
  - Text band     (25% = 375px) — title + subtitle on warm dark overlay
  - Bottom strip  (15% = 225px) — second image used as accent/footer

Layout rationale:
  - 60% hero image = maximum visual hook (Pinterest best practice)
  - Warm dark overlay (not pure black) = higher CTR for food content
  - Subtitle line below title = gives the "why click" signal
  - Site domain at bottom = brand recall without being intrusive
"""

import os
import time
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime


class PinterestPinGenerator:
    # Canvas — standard Pinterest recommended size
    CANVAS_WIDTH  = 1000
    CANVAS_HEIGHT = 1500

    # Section heights
    HERO_HEIGHT     = 900   # 60% — main food photo
    TEXT_HEIGHT     = 375   # 25% — title + subtitle
    FOOTER_HEIGHT   = 225   # 15% — second image as footer accent

    # Title text
    TITLE_FONT_SIZE    = 78
    SUBTITLE_FONT_SIZE = 42
    SITE_FONT_SIZE     = 34

    TITLE_COLOR    = (255, 255, 255)
    SUBTITLE_COLOR = (255, 220, 160)   # warm cream — readable on dark overlay
    SITE_COLOR     = (200, 200, 200)   # light grey

    # Warm dark overlay — outperforms pure black for food content CTR
    OVERLAY_COLOR = (30, 15, 5, 218)   # very dark warm brown, ~85% opacity

    TEXT_PADDING = 55
    TITLE_LINE_HEIGHT    = 100
    SUBTITLE_LINE_HEIGHT = 55

    SITE_LABEL = "chocokitchen.com"

    def __init__(self, font_path: str = None, subtitle_font_path: str = None):
        self.font_path          = font_path or self._find_system_font()
        self.subtitle_font_path = subtitle_font_path or self.font_path
        self.title_font    = self._load_font(self.font_path, self.TITLE_FONT_SIZE)
        self.subtitle_font = self._load_font(self.subtitle_font_path, self.SUBTITLE_FONT_SIZE)
        self.site_font     = self._load_font(self.subtitle_font_path, self.SITE_FONT_SIZE)

    # ------------------------------------------------------------------
    # Font helpers
    # ------------------------------------------------------------------

    def _find_system_font(self) -> str | None:
        candidates = [
            str(Path(__file__).parent.parent / "templates" / "fonts" / "Montserrat-Bold.ttf"),
            str(Path(__file__).parent.parent / "templates" / "fonts" / "Montserrat-Regular.ttf"),
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Georgia Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        for p in candidates:
            if os.path.exists(p):
                print(f"[pin] Font: {p}")
                return p
        print("[pin] No TTF found — using PIL default font")
        return None

    def _load_font(self, path: str | None, size: int):
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception as e:
                print(f"[pin] Font load error ({e}) — using default")
        return ImageFont.load_default()

    # ------------------------------------------------------------------
    # Image download with retry
    # ------------------------------------------------------------------

    def _download_image(self, url: str) -> Image.Image:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return Image.open(unquote(parsed.path)).convert("RGB")
        if not parsed.scheme and Path(url).exists():
            return Image.open(url).convert("RGB")

        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=45)
                resp.raise_for_status()
                return Image.open(BytesIO(resp.content)).convert("RGB")
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"[pin] Download attempt {attempt + 1} failed ({e}), retrying...")
                time.sleep(3 * (attempt + 1))

    def _centre_crop(self, img: Image.Image, w: int, h: int) -> Image.Image:
        img_ratio    = img.width / img.height
        target_ratio = w / h
        if img_ratio > target_ratio:
            new_w = int(img.width * (h / img.height))
            img   = img.resize((new_w, h), Image.Resampling.LANCZOS)
            left  = (new_w - w) // 2
            img   = img.crop((left, 0, left + w, h))
        else:
            new_h = int(img.height * (w / img.width))
            img   = img.resize((w, new_h), Image.Resampling.LANCZOS)
            top   = (new_h - h) // 2
            img   = img.crop((0, top, w, top + h))
        return img

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def _wrap_text(self, text: str, max_width: int, draw: ImageDraw.ImageDraw, font) -> list[str]:
        words, lines, current = text.strip().split(), [], []
        for word in words:
            test = " ".join(current + [word])
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines or [""]

    def _draw_text_band(self, canvas: Image.Image, title: str, subtitle: str):
        band_top = self.HERO_HEIGHT
        max_w    = self.CANVAS_WIDTH - (self.TEXT_PADDING * 2)

        # Compositing requires RGBA for correct alpha blending
        rgba   = canvas.convert("RGBA")
        overlay = Image.new("RGBA", (self.CANVAS_WIDTH, self.TEXT_HEIGHT), self.OVERLAY_COLOR)
        rgba.paste(overlay, (0, band_top), overlay)
        canvas.paste(rgba.convert("RGB"))

        draw          = ImageDraw.Draw(canvas)
        title_lines   = self._wrap_text(title, max_w, draw, self.title_font)
        sub_lines     = self._wrap_text(subtitle, max_w, draw, self.subtitle_font)

        title_block_h = len(title_lines) * self.TITLE_LINE_HEIGHT
        sub_block_h   = len(sub_lines) * self.SUBTITLE_LINE_HEIGHT
        site_h        = self.SITE_FONT_SIZE + 10

        # Vertical distribution: title / subtitle / site URL
        total_h  = title_block_h + 18 + sub_block_h + 18 + site_h
        start_y  = band_top + (self.TEXT_HEIGHT - total_h) // 2

        # Title lines
        y = start_y
        for line in title_lines:
            lw = draw.textbbox((0, 0), line, font=self.title_font)[2]
            x  = (self.CANVAS_WIDTH - lw) // 2
            # Shadow — solid dark on RGB canvas (alpha not supported in text fill)
            draw.text((x + 3, y + 3), line, font=self.title_font, fill=(10, 5, 0))
            draw.text((x, y),         line, font=self.title_font, fill=self.TITLE_COLOR)
            y += self.TITLE_LINE_HEIGHT

        y += 18

        # Subtitle lines
        for line in sub_lines:
            lw = draw.textbbox((0, 0), line, font=self.subtitle_font)[2]
            x  = (self.CANVAS_WIDTH - lw) // 2
            draw.text((x, y), line, font=self.subtitle_font, fill=self.SUBTITLE_COLOR)
            y += self.SUBTITLE_LINE_HEIGHT

        y += 18

        # Site label
        site_w = draw.textbbox((0, 0), self.SITE_LABEL, font=self.site_font)[2]
        draw.text(
            ((self.CANVAS_WIDTH - site_w) // 2, y),
            self.SITE_LABEL,
            font=self.site_font,
            fill=self.SITE_COLOR,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pin(
        self,
        top_image_url: str,
        bottom_image_url: str,
        title: str,
        subtitle: str = "Quick & Easy Homemade Recipe",
        output_path: str = None,
    ) -> str:
        """
        Generate a 1000x1500 Pinterest pin.

        Layout:
          - Top 60%: hero food photo (top_image_url)
          - Middle 25%: title + subtitle + site label on warm overlay
          - Bottom 15%: second image as footer accent (bottom_image_url)

        Args:
            top_image_url:    URL of the hero image (U1)
            bottom_image_url: URL of the accent footer image (U2)
            title:            Recipe title (auto-wrapped)
            subtitle:         Benefit line shown below title
            output_path:      Save path; auto-generated if None

        Returns:
            Path to the saved JPEG file
        """
        print(f"[pin] Generating pin: '{title[:60]}'")

        canvas = Image.new("RGB", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), (20, 10, 5))

        # Hero image (top 60%)
        print("[pin] Downloading hero image...")
        hero = self._centre_crop(
            self._download_image(top_image_url),
            self.CANVAS_WIDTH, self.HERO_HEIGHT,
        )
        canvas.paste(hero, (0, 0))

        # Footer accent image (bottom 15%)
        print("[pin] Downloading footer image...")
        footer = self._centre_crop(
            self._download_image(bottom_image_url),
            self.CANVAS_WIDTH, self.FOOTER_HEIGHT,
        )
        canvas.paste(footer, (0, self.HERO_HEIGHT + self.TEXT_HEIGHT))

        # Text band (middle 25%) — draw last so it sits on top
        print("[pin] Rendering text band...")
        self._draw_text_band(canvas, title, subtitle)

        # Save as JPEG (much smaller than PNG, faster, fine for Pinterest)
        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            Path("pins").mkdir(exist_ok=True)
            output_path = f"pins/pinterest_pin_{ts}.jpg"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "JPEG", quality=88, optimize=True, progressive=True)

        size_kb = Path(output_path).stat().st_size / 1024
        print(f"[pin] Saved → {output_path} ({size_kb:.0f} KB, {self.CANVAS_WIDTH}×{self.CANVAS_HEIGHT}px)")
        return output_path
