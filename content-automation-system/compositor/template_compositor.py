"""
Landscape Pinterest Pin Template Compositor
===========================================
Generates 1000x1500 Pinterest pins matching the provided example:
U1 image top, a clean white center text band, and U2 image bottom.
"""

import os
import re
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, ImageStat

from services.pin_template_registry import DEFAULT_TEMPLATE_ID, apply_pin_template_style, load_pin_template


W, H = 1000, 1500
TOP_SCENE_BOTTOM = 620
TEXT_BAND_TOP = 620
TEXT_BAND_BOTTOM = 890
BOTTOM_SCENE_TOP = 890

TEXT_ORANGE = (205, 76, 7)
WHITE = (255, 255, 255)


class TemplateCompositor:
    FONT_FAMILY_CANDIDATES = {
        "lilita one": [
            "templates/fonts/LilitaOne-Regular.ttf",
        ],
        "noto serif ethiopic condensed": [
            "templates/fonts/NotoSerifEthiopicCondensed-Bold.ttf",
            "templates/fonts/NotoSerifEthiopicCondensed-Regular.ttf",
            "/System/Library/Fonts/Supplemental/NotoSerifEthiopicCondensed-Bold.ttf",
            "/System/Library/Fonts/Supplemental/NotoSerifEthiopicCondensed-Regular.ttf",
            "/Library/Fonts/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        ],
        "canva sans": [
            "templates/fonts/CanvaSans-Bold.ttf",
            "templates/fonts/CanvaSans-Regular.ttf",
            "/Library/Fonts/Arial Rounded Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ],
        "chewy": [
            "templates/fonts/Chewy-Regular.ttf",
            "/Library/Fonts/Comic Sans MS Bold.ttf",
            "/Library/Fonts/Arial Rounded Bold.ttf",
        ],
        "arimo": [
            "templates/fonts/Arimo-Bold.ttf",
            "templates/fonts/Arimo-Regular.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/Library/Fonts/Arial.ttf",
        ],
        "impact": [
            "/Library/Fonts/Impact.ttf",
            "/System/Library/Fonts/Supplemental/Impact.ttf",
        ],
        "arial black": [
            "/System/Library/Fonts/Supplemental/Arial Black.ttf",
            "/Library/Fonts/Arial Black.ttf",
        ],
        "arial rounded": [
            "/Library/Fonts/Arial Rounded Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
        ],
        "cooper": [
            "templates/fonts/CooperBlack.ttf",
            "/System/Library/Fonts/Supplemental/Cooper Black.ttf",
            "/Library/Fonts/Cooper Black.ttf",
            "/Library/Fonts/Georgia Bold.ttf",
        ],
        "futura": [
            "/Library/Fonts/Futura.ttc",
            "/System/Library/Fonts/Supplemental/Futura.ttc",
        ],
        "georgia bold": [
            "/Library/Fonts/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        ],
        "comic sans bold": [
            "/Library/Fonts/Comic Sans MS Bold.ttf",
            "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf",
        ],
    }
    FONT_CANDIDATES = [
        str(Path(__file__).parent.parent / "templates" / "fonts" / "LilitaOne-Regular.ttf"),
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Georgia Bold.ttf",
        str(Path(__file__).parent.parent / "templates" / "fonts" / "Montserrat-Bold.ttf"),
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def __init__(self, template_id: str | None = None, style_override: dict | None = None):
        self.template_id = template_id or DEFAULT_TEMPLATE_ID
        self.template = apply_pin_template_style(load_pin_template(self.template_id), style_override)
        self.font_path = self._find_font()

    def _canvas_size(self) -> tuple[int, int]:
        canvas = self.template.get("canvas", {})
        return int(canvas.get("width", W)), int(canvas.get("height", H))

    def _layout_box(self, key: str) -> tuple[int, int, int, int]:
        box = self.template.get("layout", {}).get(key, {})
        return (
            int(box.get("x", 0)),
            int(box.get("y", 0)),
            int(box.get("width", W)),
            int(box.get("height", H)),
        )

    def _hex_color(self, value: str | tuple[int, int, int] | None, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
        if isinstance(value, tuple):
            return value
        if not value or not isinstance(value, str):
            return fallback
        value = value.strip().lstrip("#")
        if len(value) != 6:
            return fallback
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return fallback

    def _find_font(self) -> str | None:
        text_cfg = self.template.get("text", {})
        template_font = text_cfg.get("font_path")
        candidates = []
        family = str(text_cfg.get("font_family", "")).strip().lower()
        for candidate in self.FONT_FAMILY_CANDIDATES.get(family, []):
            font_path = Path(candidate)
            if not font_path.is_absolute():
                font_path = Path(__file__).parent.parent / font_path
            candidates.append(str(font_path))
        if template_font:
            font_path = Path(template_font)
            if not font_path.is_absolute():
                font_path = Path(__file__).parent.parent / font_path
            candidates.append(str(font_path))
        candidates.extend(self.FONT_CANDIDATES)

        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def _font_from_candidates(self, size: int, candidates: list[str]) -> ImageFont.FreeTypeFont:
        for path in candidates:
            if path and os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return self._font(size)

    def _font_for_family(self, family: str | None, size: int) -> ImageFont.FreeTypeFont:
        candidates: list[str] = []
        key = str(family or "").strip().lower()
        for candidate in self.FONT_FAMILY_CANDIDATES.get(key, []):
            font_path = Path(candidate)
            if not font_path.is_absolute():
                font_path = Path(__file__).parent.parent / font_path
            candidates.append(str(font_path))
        candidates.extend(self.FONT_CANDIDATES)
        return self._font_from_candidates(size, candidates)

    def _draw_cartoon_background(self, canvas: Image.Image, variant: str = "split") -> None:
        canvas_w, canvas_h = canvas.size
        draw = ImageDraw.Draw(canvas)
        sky_top = (198, 237, 252)
        sky_bottom = (238, 253, 254)
        for y in range(canvas_h):
            ratio = y / max(1, canvas_h - 1)
            color = tuple(int(sky_top[i] * (1 - ratio) + sky_bottom[i] * ratio) for i in range(3))
            draw.line((0, y, canvas_w, y), fill=color)

        def cloud(cx: int, cy: int, scale: float = 1.0):
            fill = (255, 255, 255)
            draw.ellipse((cx - int(130 * scale), cy - int(40 * scale), cx + int(120 * scale), cy + int(70 * scale)), fill=fill)
            draw.ellipse((cx - int(60 * scale), cy - int(105 * scale), cx + int(70 * scale), cy + int(65 * scale)), fill=fill)
            draw.ellipse((cx - int(185 * scale), cy - int(25 * scale), cx - int(55 * scale), cy + int(70 * scale)), fill=fill)
            draw.ellipse((cx + int(55 * scale), cy - int(15 * scale), cx + int(185 * scale), cy + int(70 * scale)), fill=fill)
            draw.rectangle((cx - int(175 * scale), cy + int(20 * scale), cx + int(170 * scale), cy + int(70 * scale)), fill=fill)

        def hills(base_y: int, bottom_y: int, dark_offset: int = 82, amp_light: int = 28, amp_dark: int = 36):
            light = (199, 231, 122)
            dark = (137, 174, 0)
            pts_light = []
            for x in range(-80, canvas_w + 100, 80):
                y = base_y + int(amp_light * __import__("math").sin((x + 80) / 155))
                pts_light.append((x, y))
            draw.polygon([(0, bottom_y)] + pts_light + [(canvas_w, bottom_y)], fill=light)
            pts_dark = []
            for x in range(-80, canvas_w + 100, 80):
                y = base_y + dark_offset + int(amp_dark * __import__("math").sin((x - 220) / 180))
                pts_dark.append((x, y))
            draw.polygon([(0, bottom_y)] + pts_dark + [(canvas_w, bottom_y)], fill=dark)

        if variant == "single":
            cloud(canvas_w // 2, 280, 1.08)
            hills(1080, canvas_h, 150, 24, 34)
            return

        cloud(canvas_w // 2, 120, 0.88)
        hills(520, 690, 90, 26, 34)
        cloud(canvas_w // 2, 925, 0.82)
        hills(1295, canvas_h, 85, 26, 34)

    def _draw_dashed_rectangle(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        fill: tuple[int, int, int],
        width: int,
        dash: int,
        gap: int,
    ) -> None:
        if width <= 0:
            return
        x1, y1, x2, y2 = box

        def dashed_line(start: tuple[int, int], end: tuple[int, int]) -> None:
            horizontal = start[1] == end[1]
            length = abs((end[0] - start[0]) if horizontal else (end[1] - start[1]))
            cursor = 0
            while cursor < length:
                segment = min(dash, length - cursor)
                if horizontal:
                    sx = start[0] + cursor if end[0] >= start[0] else start[0] - cursor
                    ex = start[0] + cursor + segment if end[0] >= start[0] else start[0] - cursor - segment
                    draw.line((sx, start[1], ex, end[1]), fill=fill, width=width)
                else:
                    sy = start[1] + cursor if end[1] >= start[1] else start[1] - cursor
                    ey = start[1] + cursor + segment if end[1] >= start[1] else start[1] - cursor - segment
                    draw.line((start[0], sy, end[0], ey), fill=fill, width=width)
                cursor += dash + gap

        inset = max(1, width // 2)
        dashed_line((x1 + inset, y1 + inset), (x2 - inset, y1 + inset))
        dashed_line((x2 - inset, y1 + inset), (x2 - inset, y2 - inset))
        dashed_line((x2 - inset, y2 - inset), (x1 + inset, y2 - inset))
        dashed_line((x1 + inset, y2 - inset), (x1 + inset, y1 + inset))

    def _download(self, url: str) -> Image.Image:
        print(f"[compositor] Downloading: {url[:80]}")
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return Image.open(unquote(parsed.path)).convert("RGB")
        if not parsed.scheme and Path(url).exists():
            return Image.open(url).convert("RGB")

        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=45)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if content_type and "image" not in content_type:
                    raise ValueError(f"URL did not return an image: {content_type}")
                return Image.open(BytesIO(resp.content)).convert("RGB")
            except Exception as exc:
                if attempt == 2:
                    raise
                print(f"[compositor] Download attempt {attempt + 1} failed ({exc}), retrying...")
                time.sleep(3 * (attempt + 1))

    def _enhance_food(self, img: Image.Image) -> Image.Image:
        image_cfg = self.template.get("image", {})
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(float(image_cfg.get("brightness", 1.04)))
        img = ImageEnhance.Contrast(img).enhance(float(image_cfg.get("contrast", 1.12)))
        img = ImageEnhance.Color(img).enhance(float(image_cfg.get("color", 1.08)))
        img = ImageEnhance.Sharpness(img).enhance(float(image_cfg.get("sharpness", 1.18)))
        return img

    def _smart_crop(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        img = self._enhance_food(img)
        target_ratio = target_w / target_h
        source_ratio = img.width / img.height

        if source_ratio > target_ratio:
            crop_h = img.height
            crop_w = int(crop_h * target_ratio)
            max_x = img.width - crop_w
            candidates = [(int(max_x * p), 0, int(max_x * p) + crop_w, crop_h) for p in (0.2, 0.35, 0.5, 0.65, 0.8)]
        else:
            crop_w = img.width
            crop_h = int(crop_w / target_ratio)
            max_y = img.height - crop_h
            candidates = [(0, int(max_y * p), crop_w, int(max_y * p) + crop_h) for p in (0.08, 0.22, 0.38, 0.54, 0.7)]

        best_box = candidates[len(candidates) // 2]
        best_score = -1.0
        for box in candidates:
            crop = img.crop(box).resize((220, 220), Image.Resampling.BICUBIC)
            brightness = sum(ImageStat.Stat(crop).mean) / 3
            saturation = ImageStat.Stat(crop.convert("HSV")).mean[1]
            edges = ImageStat.Stat(crop.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]
            score = saturation * 0.8 + edges * 1.2 - abs(brightness - 140) * 0.15
            if score > best_score:
                best_score = score
                best_box = box

        return img.crop(best_box).resize((target_w, target_h), Image.Resampling.LANCZOS)

    def _clean_title(self, title: str) -> str:
        text_cfg = self.template.get("text", {})
        text = re.sub(r"\b(easy|best|homemade)\b", "", title or "", flags=re.I)
        text = re.sub(r"[^A-Za-z0-9 '&-]+", " ", text)
        words = [word for word in text.split() if word]
        max_words = int(text_cfg.get("max_words", 12))
        cleaned = " ".join(words[:max_words]) or "TEXT"
        return cleaned.upper() if text_cfg.get("uppercase", True) else cleaned

    def _clean_title_line(self, line: str) -> str:
        text_cfg = self.template.get("text", {})
        text = re.sub(r"[^A-Za-z0-9 '&-]+", " ", line or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text.upper() if text_cfg.get("uppercase", True) else text

    def _title_words_for_layout(self, title: str) -> list[str]:
        explicit_lines = [self._clean_title_line(line) for line in re.split(r"\r?\n|\|", title or "") if line.strip()]
        explicit_lines = [line for line in explicit_lines if line]
        if explicit_lines:
            return " ".join(explicit_lines).split()
        return self._clean_title(title).split()

    def _text_width(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def _line_height(self, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        return bbox[3] - bbox[1]

    def _balanced_line_candidates(self, words: list[str], line_count: int) -> list[list[str]]:
        if line_count == 1:
            return [[" ".join(words)]]
        if len(words) < line_count:
            return []

        candidates: list[list[str]] = []

        def build(start: int, remaining: int, current: list[str]):
            if remaining == 1:
                if start < len(words):
                    candidates.append(current + [" ".join(words[start:])])
                return

            max_split = len(words) - remaining + 1
            for end in range(start + 1, max_split + 1):
                build(end, remaining - 1, current + [" ".join(words[start:end])])

        build(0, line_count, [])
        return candidates

    def balance_title_lines(
        self,
        title: str,
        draw: ImageDraw.ImageDraw,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        max_lines: int = 2,
    ) -> list[str]:
        """
        Split a title into visually balanced lines using PIL text measurement.

        Example:
            "MOIST CHOCOLATE CAKE WITH SIMPLE TIPS"
            -> ["MOIST CHOCOLATE CAKE", "WITH SIMPLE TIPS"]
        """
        words = self._title_words_for_layout(title)
        if not words:
            return ["TEXT"]

        best_lines: list[str] | None = None
        best_score: float | None = None
        max_lines = max(1, min(max_lines, int(self.template.get("text", {}).get("max_lines", 2)), len(words)))

        for line_count in range(1, max_lines + 1):
            for lines in self._balanced_line_candidates(words, line_count):
                widths = [self._text_width(draw, line, font) for line in lines]
                if max(widths) > max_width:
                    continue

                mean_width = sum(widths) / len(widths)
                raggedness = sum(abs(width - mean_width) for width in widths)
                longest_penalty = max(widths) * 0.08
                if len(words) >= 7 and max_lines >= 3:
                    line_count_penalty = 0 if line_count == 3 else 120
                elif len(words) <= 5:
                    line_count_penalty = 0 if line_count <= 2 else 140
                else:
                    line_count_penalty = 0 if line_count >= 2 else 80
                score = raggedness + longest_penalty + line_count_penalty

                if best_score is None or score < best_score:
                    best_score = score
                    best_lines = lines

        if best_lines:
            return best_lines

        # Last resort: greedy wrapping, still without splitting words.
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            candidate = " ".join(current + [word])
            if current and self._text_width(draw, candidate, font) > max_width:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines[:max_lines]

    def _fit_title_lines(
        self,
        draw: ImageDraw.ImageDraw,
        title: str,
        max_width: int,
        max_height: int,
        max_lines: int = 2,
    ) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
        text_cfg = self.template.get("text", {})
        max_size = int(text_cfg.get("font_size_max", 92))
        min_size = int(text_cfg.get("font_size_min", 42))
        min_visual_width_ratio = float(text_cfg.get("min_visual_width_ratio", 0.46))
        target_width = max_width * max(0.4, min(0.6, min_visual_width_ratio))
        line_spacing = float(text_cfg.get("line_spacing", 1.22))
        fallback_fit: tuple[ImageFont.FreeTypeFont, list[str], int] | None = None
        title_words = self._title_words_for_layout(title)
        for size in range(max_size, min_size - 1, -4):
            font = self._font(size)
            lines = self.balance_title_lines(title, draw, font, max_width, max_lines=max_lines)
            rendered_words = " ".join(lines).split()
            if rendered_words != title_words[: len(rendered_words)] or len(rendered_words) < len(title_words):
                continue
            widths = [self._text_width(draw, line, font) for line in lines]
            line_h = int(self._line_height(draw, font) * line_spacing)
            total_h = len(lines) * line_h
            if len(lines) <= max_lines and total_h <= max_height and all(width <= max_width for width in widths):
                fit = (font, lines, line_h)
                if fallback_fit is None:
                    fallback_fit = fit
                if max(widths or [0]) >= target_width:
                    return fit

        if fallback_fit is not None:
            return fallback_fit

        font = self._font(min_size)
        lines = self.balance_title_lines(title, draw, font, max_width, max_lines=max_lines)
        lines = lines[:max_lines]
        while min_size > 18 and any(self._text_width(draw, line, font) > max_width for line in lines):
            min_size -= 2
            font = self._font(min_size)
            lines = self.balance_title_lines(title, draw, font, max_width, max_lines=max_lines)[:max_lines]
        return font, lines, int(self._line_height(draw, font) * line_spacing)

    def _draw_center_text(self, draw: ImageDraw.ImageDraw, title: str, canvas_w: int):
        text_cfg = self.template.get("text", {})
        band_cfg = self.template.get("layout", {}).get("text_band", {})
        badge_cfg = self.template.get("layout", {}).get("text_badge", {})
        accent_cfg = self.template.get("layout", {}).get("accent_text", {})
        eyebrow_cfg = self.template.get("layout", {}).get("eyebrow_text", {})
        tagline_cfg = self.template.get("layout", {}).get("tagline_text", {})
        band_x, band_y, band_w, band_h = self._layout_box("text_band")
        bg = self._hex_color(band_cfg.get("background"), WHITE)
        border = self._hex_color(band_cfg.get("border_color"), WHITE)
        border_w = int(band_cfg.get("border_width", 0))
        border_style = str(band_cfg.get("border_style", "solid")).lower()
        radius = int(band_cfg.get("radius", 0))

        band_box = (band_x, band_y, band_x + band_w, band_y + band_h)
        if radius > 0:
            draw.rounded_rectangle(band_box, radius=radius, fill=bg)
        else:
            draw.rectangle(band_box, fill=bg)
        if border_w > 0:
            if border_style == "dashed":
                self._draw_dashed_rectangle(
                    draw,
                    band_box,
                    border,
                    border_w,
                    int(band_cfg.get("border_dash", 18)),
                    int(band_cfg.get("border_gap", 12)),
                )
            else:
                for i in range(border_w):
                    outline_box = (band_x + i, band_y + i, band_x + band_w - i - 1, band_y + band_h - i - 1)
                    if radius > 0:
                        draw.rounded_rectangle(outline_box, radius=max(0, radius - i), outline=border)
                    else:
                        draw.rectangle(outline_box, outline=border)

        padding_x = int(text_cfg.get("safe_padding_x", 90))
        padding_y = int(text_cfg.get("safe_padding_y", 44))
        max_w = band_w - (padding_x * 2)
        eyebrow_text = str(eyebrow_cfg.get("text", "")).strip() if eyebrow_cfg.get("enabled") else ""
        tagline_text = str(tagline_cfg.get("text", "")).strip() if tagline_cfg.get("enabled") else ""
        eyebrow_font = self._font_for_family(eyebrow_cfg.get("font_family"), int(eyebrow_cfg.get("font_size", 30))) if eyebrow_text else None
        tagline_font = self._font_for_family(tagline_cfg.get("font_family"), int(tagline_cfg.get("font_size", 32))) if tagline_text else None
        eyebrow_h = self._line_height(draw, eyebrow_font) if eyebrow_font else 0
        tagline_h = self._line_height(draw, tagline_font) if tagline_font else 0
        eyebrow_gap = int(eyebrow_cfg.get("gap", 16)) if eyebrow_text else 0
        tagline_gap = int(tagline_cfg.get("gap", 16)) if tagline_text else 0
        badge_enabled = bool(badge_cfg.get("enabled", False))
        badge_text = str(badge_cfg.get("text", "")).strip()
        badge_h = int(badge_cfg.get("height", 0)) if badge_enabled and badge_text else 0
        badge_absolute = "absolute_y" in badge_cfg
        badge_gap = 0 if badge_absolute else (int(badge_cfg.get("gap", 16)) if badge_h else 0)
        reserved_badge_h = int(badge_h * 0.55) if badge_absolute else badge_h + badge_gap
        max_h = band_h - (padding_y * 2) - reserved_badge_h - eyebrow_h - eyebrow_gap - tagline_h - tagline_gap
        max_lines = int(text_cfg.get("max_lines", 2))
        if max_lines < 2 and len(self._clean_title(title).split()) > 3:
            max_lines = 2
        font, lines, line_h = self._fit_title_lines(draw, title, max_w, max_h, max_lines=max_lines)
        title_h = len(lines) * line_h
        total_h = eyebrow_h + eyebrow_gap + title_h + tagline_gap + tagline_h + (0 if badge_absolute else badge_gap + badge_h)
        y = band_y + (band_h - total_h) // 2 - 4
        fill = self._hex_color(text_cfg.get("fill"), TEXT_ORANGE)
        stroke_fill = self._hex_color(text_cfg.get("stroke_fill"), fill)
        stroke_w = int(text_cfg.get("stroke_width", 0))
        shadow_fill = self._hex_color(text_cfg.get("shadow_fill"), (158, 52, 6))
        shadow_offset = text_cfg.get("shadow_offset", [3, 4])
        shadow_x, shadow_y = int(shadow_offset[0]), int(shadow_offset[1])

        if accent_cfg.get("enabled"):
            accent_text = str(accent_cfg.get("text", "")).strip()
            if accent_text:
                accent_candidates = [
                    "/System/Library/Fonts/Supplemental/Snell Roundhand.ttc",
                    "/System/Library/Fonts/Supplemental/SignPainter.ttc",
                    "/Library/Fonts/Georgia Italic.ttf",
                    "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
                ]
                accent_font = self._font_from_candidates(int(accent_cfg.get("font_size", 116)), accent_candidates)
                accent_fill = self._hex_color(accent_cfg.get("fill"), (255, 200, 0))
                accent_stroke = self._hex_color(accent_cfg.get("stroke_fill"), (0, 0, 0))
                accent_stroke_w = int(accent_cfg.get("stroke_width", 3))
                accent_w = self._text_width(draw, accent_text, accent_font)
                accent_x = int(accent_cfg.get("x", band_x + (band_w - accent_w) // 2))
                accent_y = int(accent_cfg.get("y", band_y - 88))
                draw.text(
                    (accent_x, accent_y),
                    accent_text,
                    font=accent_font,
                    fill=accent_fill,
                    stroke_width=accent_stroke_w,
                    stroke_fill=accent_stroke,
                )

        if eyebrow_text and eyebrow_font:
            eyebrow_fill = self._hex_color(eyebrow_cfg.get("fill"), (140, 145, 136))
            eyebrow = eyebrow_text.upper()
            text_w = self._text_width(draw, eyebrow, eyebrow_font)
            draw.text((band_x + (band_w - text_w) // 2, y), eyebrow, font=eyebrow_font, fill=eyebrow_fill)
            y += eyebrow_h + eyebrow_gap

        for line in lines:
            text_w = self._text_width(draw, line, font)
            x = band_x + (band_w - text_w) // 2
            if shadow_x or shadow_y:
                draw.text((x + shadow_x, y + shadow_y), line, font=font, fill=shadow_fill, stroke_width=stroke_w, stroke_fill=stroke_fill)
            draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=stroke_fill)
            y += line_h

        if tagline_text and tagline_font:
            y += tagline_gap
            tagline_fill = self._hex_color(tagline_cfg.get("fill"), (162, 166, 157))
            text_w = self._text_width(draw, tagline_text, tagline_font)
            draw.text((band_x + (band_w - text_w) // 2, y), tagline_text, font=tagline_font, fill=tagline_fill)
            y += tagline_h

        if badge_h and badge_text:
            badge_w = int(badge_cfg.get("width", min(480, band_w - 160)))
            radius = int(badge_cfg.get("radius", 14))
            badge_bg = self._hex_color(badge_cfg.get("background"), (143, 63, 31))
            badge_fill = self._hex_color(badge_cfg.get("fill"), WHITE)
            badge_border = self._hex_color(badge_cfg.get("border_color"), badge_bg)
            badge_border_w = int(badge_cfg.get("border_width", 0))
            badge_font = self._font_for_family(badge_cfg.get("font_family") or text_cfg.get("font_family"), int(badge_cfg.get("font_size", 34)))
            badge_x = band_x + (band_w - badge_w) // 2
            badge_y = int(badge_cfg.get("absolute_y", y + badge_gap))
            badge_box = (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h)
            draw.rounded_rectangle(
                badge_box,
                radius=radius,
                fill=badge_bg,
            )
            if badge_border_w > 0:
                for i in range(badge_border_w):
                    draw.rounded_rectangle(
                        (badge_box[0] + i, badge_box[1] + i, badge_box[2] - i - 1, badge_box[3] - i - 1),
                        radius=max(0, radius - i),
                        outline=badge_border,
                    )
            badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
            text_w = badge_bbox[2] - badge_bbox[0]
            text_h = badge_bbox[3] - badge_bbox[1]
            text_x = badge_x + (badge_w - text_w) // 2
            text_y = badge_y + (badge_h - text_h) // 2 - badge_bbox[1]
            draw.text((text_x, text_y), badge_text, font=badge_font, fill=badge_fill)

    def generate_pin(
        self,
        top_image_url: str,
        bottom_image_url: str,
        title: str,
        output_path: str = None,
    ) -> str:
        """
        Generate a 1000x1500 screenshot-style Pinterest pin with U1 on top
        and U2 on the bottom.
        """
        canvas_w, canvas_h = self._canvas_size()
        canvas_bg = self._hex_color(self.template.get("canvas", {}).get("background"), WHITE)
        print(f"[compositor] Building {self.template.get('label', self.template_id)} pin: '{title[:60]}'")
        canvas = Image.new("RGB", (canvas_w, canvas_h), canvas_bg)
        draw = ImageDraw.Draw(canvas)

        scene_cfg = self.template.get("scene", {})
        if scene_cfg.get("type") == "cartoon_hills":
            self._draw_cartoon_background(canvas, str(scene_cfg.get("variant", "split")))

        top_cfg = self.template.get("layout", {}).get("top_image", {})
        bottom_cfg = self.template.get("layout", {}).get("bottom_image", {})
        top_x, top_y, top_w, top_h = self._layout_box("top_image")
        bottom_x, bottom_y, bottom_w, bottom_h = self._layout_box("bottom_image")

        if top_cfg.get("enabled", True):
            top_img = self._smart_crop(self._download(top_image_url), top_w, top_h)
            canvas.paste(top_img, (top_x, top_y))
        if bottom_cfg.get("enabled", True):
            bottom_img = self._smart_crop(self._download(bottom_image_url), bottom_w, bottom_h)
            canvas.paste(bottom_img, (bottom_x, bottom_y))
        self._draw_center_text(draw, title, canvas_w)

        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            Path("pins").mkdir(exist_ok=True)
            output_path = f"pins/pin_{ts}.jpg"
        elif output_path.lower().endswith(".png"):
            output_path = output_path[:-4] + ".jpg"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        export_cfg = self.template.get("export", {})
        canvas.save(
            output_path,
            export_cfg.get("format", "JPEG"),
            quality=int(export_cfg.get("quality", 90)),
            optimize=bool(export_cfg.get("optimize", True)),
            progressive=bool(export_cfg.get("progressive", True)),
        )

        size_kb = Path(output_path).stat().st_size / 1024
        print(f"[compositor] Saved -> {output_path} ({size_kb:.0f} KB, {canvas_w}x{canvas_h}px)")
        return output_path
