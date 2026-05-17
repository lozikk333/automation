import re
import base64
import binascii
import hashlib
from datetime import date
from shutil import copy2
from html import escape
from pathlib import Path
from typing import Iterable


def _article_rating(title: str) -> tuple[str, int]:
    """Return a deterministic (rating, count) pair for a given article title."""
    h = int(hashlib.md5(title.encode()).hexdigest(), 16)
    rating = round(4.2 + (h % 1000) / 1000 * 0.8, 1)   # 4.2 – 5.0
    count  = 85 + (h >> 10) % 366                        # 85 – 450
    return str(rating), count


def _normalize_site_name(name: str) -> str:
    """Convert site name to Title Case (each word capitalized)."""
    if not name:
        return name
    return " ".join(word.capitalize() for word in name.strip().lower().split())


PAGE_SLUGS = {
    "home": "index.html",
    "about": "about.html",
    "contact": "contact.html",
    "privacy": "privacy-policy.html",
    "terms": "terms-of-use.html",
    "disclaimer": "disclaimer.html",
}

CATEGORY_RECIPES = {
    "Breakfast": [
        ("Protein French Toast", "20 min", "Boost your morning with this protein French toast. A simple, nutritious breakfast that feels special."),
        ("Egg Roll Chicken Bowl", "25 min", "A quick and healthy breakfast option with all the flavors of an egg roll, conveniently served."),
        ("Chicken and Waffles Brunch", "35 min", "Golden waffles, tender chicken, and cozy weekend flavor for a generous brunch table."),
        ("Blueberry Protein Smoothie", "10 min", "A creamy breakfast smoothie with bright berries and easy everyday ingredients."),
        ("Cinnamon Apple Oats", "18 min", "Cozy oats with tender apples and a warm cinnamon finish."),
        ("Savory Breakfast Tacos", "25 min", "Warm tortillas filled with eggs, herbs, and fresh toppings."),
    ],
    "Lunch": [
        ("Chinese Noodle Soup", "35 min", "A comforting Chinese noodle soup that's easy to make at home, perfect for a quick lunch."),
        ("Korean Cucumber Salad", "15 min", "A refreshing and simple Korean cucumber salad that's perfect for lunch or as a side dish."),
        ("Bean Sprout Salad", "15 min", "A refreshing and crunchy bean sprout salad that is perfect for a light lunch."),
        ("Tiger Salad", "15 min", "A refreshing and crunchy tiger salad that's perfect for a light, colorful lunch."),
        ("Potsticker Soup", "30 min", "A comforting and simple potsticker soup, perfect for a cozy lunch."),
        ("Chinese Chicken Salad", "30 min", "A crisp and refreshing Chinese chicken salad that's full of flavor and crunch."),
        ("Tzatziki Chicken Salad", "35 min", "A refreshing and easy tzatziki chicken salad with herbs, tomatoes, and creamy dressing."),
        ("Loaded Potato Salad", "35 min", "This loaded potato salad is a simple and delicious lunch with a cozy finish."),
    ],
    "Dinner": [
        ("Miso Eggplant", "35 min", "Savor the flavors of this simple yet delicious miso eggplant dish, perfect for a cozy dinner."),
        ("Yakisoba Noodles", "30 min", "A simple and delicious recipe for yakisoba noodles that brings the taste of Japan to your table."),
        ("Korean Spicy Chicken Stir Fry", "35 min", "Enjoy a quick and flavorful Korean spicy chicken stir fry with tender chicken and vegetables."),
        ("Sticky Garlic Chicken Noodles", "35 min", "A quick and delicious noodle dish with sticky garlic chicken, perfect for a weeknight dinner."),
        ("Bang Bang Chicken Bowl", "30 min", "A saucy chicken bowl with fresh crunch, creamy heat, and a restaurant-style finish."),
        ("Honey BBQ Chicken", "40 min", "Tender chicken glazed with honey barbecue flavor for an easy family dinner."),
    ],
    "Dessert": [
        ("Pumpkin Bread", "1 hr 15 min", "A soft loaf with warm spice and a tender crumb."),
        ("Oatmeal Cookies", "27 min", "Classic cookies with chewy centers and golden edges."),
        ("Chocolate Cake", "55 min", "A tender cake with rich chocolate flavor and a polished bakery-style crumb."),
        ("Banana Bread", "1 hr", "A cozy banana bread with a soft crumb and simple pantry ingredients."),
        ("Mulberry Cobbler", "45 min", "Juicy berries baked under a golden topping for an easy seasonal dessert."),
        ("Graduation Cake", "1 hr 30 min", "A celebration cake idea with a sweet finish and simple decorating cues."),
    ],
}

RECIPE_IMAGES = {
    "Protein French Toast": "chicken-and-waffles-brunch-set-up.jpg",
    "Egg Roll Chicken Bowl": "bang-bang-chicken-bowl-healthy.jpg",
    "Chicken and Waffles Brunch": "chicken-and-waffles-brunch-board.jpg",
    "Blueberry Protein Smoothie": "protien-smoothie-blueberry.jpg",
    "Korean Cucumber Salad": "watermelon-cucumber-salad-with-basil.jpg",
    "Bean Sprout Salad": "pasta-salad-recipe-italian-easy.jpg",
    "Watermelon Cucumber Salad": "watermelon-cucumber-salad-recipe.jpg",
    "Chicken Pasta Salad": "chicken-pasta-salad-recipe-cold.jpg",
    "Strawberry Chicken Salad": "strawberry-chicken-salad-recipe.jpg",
    "Grilled Corn Salad": "grilled-corn-salad.jpg",
    "Miso Eggplant": "grilled-chicken-side-dishe-healthy.jpg",
    "Chinese Noodle Soup": "summer-soup-recipe-vegetarian.jpg",
    "Yakisoba Noodles": "pasta-recipe-with-tomato-and-beef.jpg",
    "Korean Spicy Chicken Stir Fry": "bang-bang-chicken-bowl-recipe.jpg",
    "Sticky Garlic Chicken Noodles": "summer-chicken-pasta-salad.jpg",
    "Bang Bang Chicken Bowl": "bang-bang-chicken-bowl-easy.jpg",
    "Honey BBQ Chicken": "honey-bbq-chicken-recipe.jpg",
    "Tiger Salad": "watermelon-cucumber-salad-balsamic.jpg",
    "Potsticker Soup": "summer-soup-slow-cooker.jpg",
    "Chinese Chicken Salad": "strawberry-chicken-salad-recipe.jpg",
    "Tzatziki Chicken Salad": "strawberry-chicken-salad-sandwich.jpg",
    "Loaded Potato Salad": "chicken-smoked-turkey-ranch-pasta-salad-recipe.jpg",
    "Pumpkin Bread": "banana-bread.jpg",
    "Oatmeal Cookies": "graduation-cookies-pink.jpg",
    "Chocolate Cake": "chocolate-cake.jpg",
    "Banana Bread": "banana-bread.jpg",
    "Mulberry Cobbler": "mulberry-recipe-cobbler.jpg",
    "Graduation Cake": "graduation-cake-design-simple.jpg",
}


DEFAULT_NICHE_CATEGORIES: dict[str, list[str]] = {
    "recipes":         ["Breakfast", "Lunch", "Dinner", "Dessert", "Healthy", "Quick Meals"],
    "health":          ["Wellness", "Nutrition", "Supplements", "Fitness"],
    "fitness":         ["Workouts", "Nutrition", "Weight Loss", "Mindfulness"],
    "finance":         ["Investing", "Budgeting", "Saving", "Credit Cards"],
    "technology":      ["AI", "Software", "Gadgets", "Tutorials"],
    "travel":          ["Destinations", "Tips", "Budget Travel", "Food"],
    "education":       ["Study Tips", "Career", "Online Learning", "Productivity"],
    "general blog":    ["Lifestyle", "Personal", "Reviews", "Tips"],
    "product reviews": ["Electronics", "Home", "Beauty", "Fashion"],
    "business":        ["Entrepreneurship", "Marketing", "Finance", "Productivity"],
}

SOCIAL_PLATFORM_LABELS: dict[str, str] = {
    "facebook":  "Facebook",
    "instagram": "Instagram",
    "pinterest": "Pinterest",
    "twitter":   "X / Twitter",
    "tiktok":    "TikTok",
    "youtube":   "YouTube",
    "linkedin":  "LinkedIn",
}

# ── Color themes ──────────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {
    "Warm Editorial": {
        "primary":       "#C96A3D",
        "secondary":     "#F7F1EB",
        "accent":        "#8B4513",
        "background":    "#FFFFFF",
        "surface":       "#FFF8F3",
        "textPrimary":   "#1F1F1F",
        "textSecondary": "#5C5C5C",
        "border":        "#E8D8CC",
        "footer":        "#2A1408",
        "footerText":    "#C4A896",
    },
    "Sage Healthy": {
        "primary":       "#6B8E6B",
        "secondary":     "#F3F8F2",
        "accent":        "#4D6B4D",
        "background":    "#FFFFFF",
        "surface":       "#F3F8F2",
        "textPrimary":   "#1A211A",
        "textSecondary": "#526052",
        "border":        "#D0E0CE",
        "footer":        "#0E1A0E",
        "footerText":    "#8EAA8E",
    },
    "Midnight Authority": {
        "primary":       "#1E3A5F",
        "secondary":     "#F5F7FA",
        "accent":        "#0F172A",
        "background":    "#FFFFFF",
        "surface":       "#F5F7FA",
        "textPrimary":   "#0F172A",
        "textSecondary": "#475569",
        "border":        "#CBD5E1",
        "footer":        "#0A0F1A",
        "footerText":    "#94A3B8",
    },
    "Dessert Rose": {
        "primary":       "#D9778A",
        "secondary":     "#FFF5F7",
        "accent":        "#A84F63",
        "background":    "#FFFFFF",
        "surface":       "#FFF5F7",
        "textPrimary":   "#1F1016",
        "textSecondary": "#6B4050",
        "border":        "#F0C8D0",
        "footer":        "#1A0810",
        "footerText":    "#C4909A",
    },
    "Minimal Charcoal": {
        "primary":       "#2D2D2D",
        "secondary":     "#FAFAFA",
        "accent":        "#111111",
        "background":    "#FFFFFF",
        "surface":       "#F6F6F6",
        "textPrimary":   "#111111",
        "textSecondary": "#555555",
        "border":        "#E0E0E0",
        "footer":        "#111111",
        "footerText":    "#AAAAAA",
    },
}

NICHE_DEFAULT_THEME: dict[str, str] = {
    "recipes":         "Warm Editorial",
    "desserts":        "Dessert Rose",
    "health":          "Sage Healthy",
    "fitness":         "Sage Healthy",
    "finance":         "Midnight Authority",
    "technology":      "Midnight Authority",
    "travel":          "Minimal Charcoal",
    "education":       "Midnight Authority",
    "general blog":    "Minimal Charcoal",
    "product reviews": "Minimal Charcoal",
    "business":        "Midnight Authority",
}


def _resolve_theme(site: dict) -> dict:
    """Return a full theme dict: explicit theme_config > niche default > Warm Editorial."""
    explicit = site.get("theme_config")
    if isinstance(explicit, dict) and explicit.get("primary"):
        base_name = explicit.get("name", "")
        base = THEMES.get(base_name, THEMES["Warm Editorial"]).copy()
        base.update({k: v for k, v in explicit.items() if k != "name" and v})
        return base
    niche = (site.get("niche_type") or "recipes").lower()
    theme_name = NICHE_DEFAULT_THEME.get(niche, "Warm Editorial")
    return THEMES[theme_name].copy()


def _theme_css(theme: dict) -> str:
    """Generate a CSS :root block that maps semantic theme vars to design tokens."""
    p   = theme.get("primary",       "#C96A3D")
    sec = theme.get("secondary",     "#F7F1EB")
    acc = theme.get("accent",        "#8B4513")
    bg  = theme.get("background",    "#FFFFFF")
    sur = theme.get("surface",       "#FFF8F3")
    tp  = theme.get("textPrimary",   "#1F1F1F")
    ts  = theme.get("textSecondary", "#5C5C5C")
    bor = theme.get("border",        "#E8D8CC")
    ftr = theme.get("footer",        "#2A1408")
    ftxt = theme.get("footerText",   "#C4A896")
    return f"""
  /* ── Theme color tokens ── */
  --color-primary:       {p};
  --color-secondary:     {sec};
  --color-accent:        {acc};
  --color-background:    {bg};
  --color-surface:       {sur};
  --color-text-primary:  {tp};
  --color-text-secondary:{ts};
  --color-border:        {bor};

  /* Map design tokens → theme */
  --gold:         var(--color-primary);
  --gold-light:   var(--color-primary);
  --gold-pale:    var(--color-surface);
  --green:        var(--color-accent);
  --green-dark:   var(--color-accent);
  --line:         var(--color-border);
  --line-soft:    var(--color-secondary);
  --cream:        var(--color-surface);
  --paper:        var(--color-background);
  --ink:          var(--color-text-primary);
  --ink-soft:     var(--color-text-primary);
  --muted:        var(--color-text-secondary);
  --muted-light:  var(--color-text-secondary);
  --footer:       {ftr};
  --footer-text:  {ftxt};"""


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "recipe-site"


def _parse_minutes(time_str: str) -> int:
    """Parse a human time string like '35 min' or '1 hr 15 min' → total minutes."""
    s = (time_str or "").lower()
    hours = 0
    mins = 0
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    if h:
        hours = int(h.group(1))
    if m:
        mins = int(m.group(1))
    return hours * 60 + mins


def _format_minutes(total: int) -> str:
    """Format integer minutes back to a readable string."""
    if total <= 0:
        return "—"
    if total < 60:
        return f"{total} min"
    h, m = divmod(total, 60)
    return f"{h} hr {m} min" if m else f"{h} hr"


def _iso_duration(minutes: int) -> str:
    """Convert minutes to ISO 8601 duration for schema.org (e.g. PT35M, PT1H15M)."""
    if minutes <= 0:
        return "PT0M"
    h, m = divmod(minutes, 60)
    return f"PT{h}H{m}M" if h else f"PT{m}M"


def _derive_times(total_str: str) -> tuple[int, int, int]:
    """Return (prep_mins, cook_mins, total_mins) derived from a total time string.

    Prep is roughly 30% of total (min 5, max 30). Cook is the remainder.
    """
    total = _parse_minutes(total_str)
    if total <= 0:
        return 10, 20, 30
    prep = max(5, min(30, round(total * 0.30 / 5) * 5))
    cook = total - prep
    return prep, cook, total


def _json_str(value: str) -> str:
    """Escape a string for safe inline JSON embedding."""
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _paragraphs(text: str) -> str:
    parts = [part.strip() for part in re.split(r"\n{2,}|\r?\n", text or "") if part.strip()]
    return "\n".join(f"<p>{escape(part)}</p>" for part in parts)


def _uploaded_asset(data_url: str | None, name: str) -> tuple[str, bytes] | None:
    if not data_url:
        return None
    match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", data_url)
    if not match:
        raise ValueError(f"{name} must be an uploaded image file")
    mime_type, encoded = match.groups()
    extensions = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/x-icon": ".ico",
        "image/vnd.microsoft.icon": ".ico",
    }
    extension = extensions.get(mime_type.lower())
    if not extension:
        raise ValueError(f"{name} must be a JPG, PNG, WebP, SVG, GIF, or ICO image")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{name} could not be decoded") from exc
    if len(data) > 5 * 1024 * 1024:
        raise ValueError(f"{name} must be 5 MB or smaller")
    return f"{name}{extension}", data


def _asset_img(filename: str | None, alt: str, class_name: str, prefix: str = "") -> str:
    if not filename:
        return ""
    return f'<img class="{class_name}" src="{prefix}assets/{escape(filename)}" alt="{escape(alt)}">'


def _php_string(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace("'", "\\'")


def _static_publish_api_php(api_key_hash: str, site_name: str) -> str:
    api_hash = _php_string(api_key_hash)
    site_label = _php_string(site_name)
    return f"""<?php
declare(strict_types=1);

const AUTOMATION_SITE_NAME = '{site_label}';
const AUTOMATION_API_KEY_HASH = '{api_hash}';
const AUTOMATION_RATE_LIMIT_SECONDS = 2;

function respond_json(int $status, array $payload): void {{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($payload, JSON_UNESCAPED_SLASHES);
    exit;
}}

function bearer_token(): string {{
    $header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    if (stripos($header, 'Bearer ') !== 0) {{
        return '';
    }}
    return trim(substr($header, 7));
}}

function slugify_text(string $value): string {{
    $value = strtolower(trim($value));
    $value = preg_replace('/[^a-z0-9]+/', '-', $value) ?? '';
    $value = trim($value, '-');
    return $value !== '' ? $value : 'article-' . date('YmdHis');
}}

function safe_html(string $html): string {{
    $html = preg_replace('#<script\\b[^>]*>.*?</script>#is', '', $html) ?? '';
    $html = preg_replace('/\\son[a-z]+\\s*=\\s*([\"\\']).*?\\1/is', '', $html) ?? '';
    return $html;
}}

function write_file_atomic(string $path, string $content): void {{
    $dir = dirname($path);
    if (!is_dir($dir) && !mkdir($dir, 0755, true)) {{
        respond_json(500, ['ok' => false, 'message' => 'Could not create directory']);
    }}
    $tmp = $path . '.tmp';
    if (file_put_contents($tmp, $content, LOCK_EX) === false || !rename($tmp, $path)) {{
        respond_json(500, ['ok' => false, 'message' => 'Could not write file']);
    }}
}}

function page_shell(string $title, string $metaDescription, string $body): string {{
    $safeTitle = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $safeMeta = htmlspecialchars($metaDescription, ENT_QUOTES, 'UTF-8');
    $siteName = htmlspecialchars(AUTOMATION_SITE_NAME, ENT_QUOTES, 'UTF-8');
    return "<!doctype html>\\n<html lang=\\"en\\">\\n<head>\\n  <meta charset=\\"utf-8\\">\\n  <meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">\\n  <title>$safeTitle | $siteName</title>\\n  <meta name=\\"description\\" content=\\"$safeMeta\\">\\n  <link rel=\\"stylesheet\\" href=\\"../../style.css\\">\\n</head>\\n<body>\\n  <main class=\\"policy-page\\">\\n    <article class=\\"article-section\\">\\n      <h1>$safeTitle</h1>\\n      $body\\n    </article>\\n  </main>\\n</body>\\n</html>\\n";
}}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {{
    respond_json(200, ['ok' => true, 'site' => AUTOMATION_SITE_NAME, 'apiEnabled' => true]);
}}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {{
    respond_json(405, ['ok' => false, 'message' => 'Method not allowed']);
}}

$token = bearer_token();
if ($token === '' || !hash_equals(AUTOMATION_API_KEY_HASH, hash('sha256', $token))) {{
    respond_json(401, ['ok' => false, 'message' => 'Unauthorized']);
}}

$rateFile = __DIR__ . '/.publish-rate';
$now = time();
$last = is_file($rateFile) ? (int) trim((string) file_get_contents($rateFile)) : 0;
if ($last > 0 && ($now - $last) < AUTOMATION_RATE_LIMIT_SECONDS) {{
    respond_json(429, ['ok' => false, 'message' => 'Rate limit exceeded']);
}}
file_put_contents($rateFile, (string) $now, LOCK_EX);

$raw = file_get_contents('php://input');
$data = json_decode($raw ?: '', true);
if (!is_array($data)) {{
    respond_json(400, ['ok' => false, 'message' => 'Invalid JSON payload']);
}}

$title = trim((string) ($data['title'] ?? ''));
$contentHtml = trim((string) ($data['contentHtml'] ?? ''));
if ($title === '' || $contentHtml === '') {{
    respond_json(422, ['ok' => false, 'message' => 'title and contentHtml are required']);
}}

$slug = slugify_text((string) ($data['slug'] ?? $title));
$metaTitle = trim((string) ($data['metaTitle'] ?? $title));
$metaDescription = trim((string) ($data['metaDescription'] ?? ''));
$category = trim((string) ($data['category'] ?? ''));
$publishDate = trim((string) ($data['publishDate'] ?? date('c')));
$featuredImage = trim((string) ($data['featuredImage'] ?? ''));
$body = safe_html($contentHtml);
if ($featuredImage !== '') {{
    $safeImage = htmlspecialchars($featuredImage, ENT_QUOTES, 'UTF-8');
    $safeAlt = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $body = "<img class=\\"recipe-hero-image\\" src=\\"$safeImage\\" alt=\\"$safeAlt\\">\\n" . $body;
}}

$root = realpath(__DIR__ . '/../..');
if ($root === false) {{
    respond_json(500, ['ok' => false, 'message' => 'Site root not found']);
}}

$articleDir = $root . '/article/' . $slug;
$articlePath = $articleDir . '/index.html';
write_file_atomic($articlePath, page_shell($metaTitle, $metaDescription, $body));

$indexPath = $root . '/index.html';
if (is_file($indexPath)) {{
    $indexHtml = (string) file_get_contents($indexPath);
    $safeTitle = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $safeDesc = htmlspecialchars($metaDescription, ENT_QUOTES, 'UTF-8');
    $safeDate = htmlspecialchars($publishDate, ENT_QUOTES, 'UTF-8');
    $safeCategory = htmlspecialchars($category, ENT_QUOTES, 'UTF-8');
    $card = "<article class=\\"recipe-card automation-post\\"><a href=\\"article/$slug/\\"><div class=\\"recipe-body\\"><p class=\\"eyebrow\\">$safeCategory</p><h3>$safeTitle</h3><p>$safeDesc</p><div class=\\"recipe-meta\\"><b>$safeDate</b></div></div></a></article>";
    if (strpos($indexHtml, '<!-- automation-recent-posts -->') !== false) {{
        $indexHtml = str_replace('<!-- automation-recent-posts -->', "<!-- automation-recent-posts -->\\n" . $card, $indexHtml);
        write_file_atomic($indexPath, $indexHtml);
    }}
}}

$sitemapPath = $root . '/sitemap.xml';
$publicUrl = '/article/' . $slug . '/';
$entry = "  <url><loc>" . htmlspecialchars($publicUrl, ENT_XML1, 'UTF-8') . "</loc><lastmod>" . date('c') . "</lastmod></url>\\n";
if (is_file($sitemapPath)) {{
    $sitemap = (string) file_get_contents($sitemapPath);
    if (strpos($sitemap, $publicUrl) === false) {{
        $sitemap = str_replace('</urlset>', $entry . '</urlset>', $sitemap);
        write_file_atomic($sitemapPath, $sitemap);
    }}
}} else {{
    write_file_atomic($sitemapPath, "<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?>\\n<urlset xmlns=\\"http://www.sitemaps.org/schemas/sitemap/0.9\\">\\n" . $entry . "</urlset>\\n");
}}

respond_json(201, ['ok' => true, 'slug' => $slug, 'url' => $publicUrl, 'path' => 'article/' . $slug . '/index.html']);
"""


def _list(items: Iterable[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return "".join(f"<li>{escape(item)}</li>" for item in cleaned)


def _yes(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r"[,;\n]+", text) if item.strip()]


def _metadata_value(metadata: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _privacy_regions(country: str) -> tuple[bool, bool]:
    value = (country or "").strip().lower()
    eu_terms = {
        "eu", "european union", "eea", "austria", "belgium", "bulgaria", "croatia",
        "cyprus", "czech republic", "czechia", "denmark", "estonia", "finland",
        "france", "germany", "greece", "hungary", "ireland", "italy", "latvia",
        "lithuania", "luxembourg", "malta", "netherlands", "poland", "portugal",
        "romania", "slovakia", "slovenia", "spain", "sweden", "iceland",
        "liechtenstein", "norway",
    }
    uk_terms = {"uk", "united kingdom", "great britain", "england", "scotland", "wales", "northern ireland"}
    us_terms = {"us", "usa", "united states", "united states of america", "california", "ca"}
    return value in eu_terms or value in uk_terms, value in us_terms


def _jurisdiction_flags(country: str) -> tuple[bool, bool, bool]:
    value = (country or "").strip().lower()
    uk_terms = {"uk", "united kingdom", "great britain", "england", "scotland", "wales", "northern ireland"}
    us_terms = {"us", "usa", "united states", "united states of america", "california", "ca"}
    is_uk = value in uk_terms
    is_us = value in us_terms
    is_eu = _privacy_regions(country)[0] and not is_uk
    return is_eu, is_us, is_uk


def _privacy_policy_sections(metadata: dict) -> tuple[dict, str]:
    site_name = _metadata_value(metadata, "siteName", "site_name", "website_name", default="Website")
    domain = _metadata_value(metadata, "domain", "base_url", default=slugify(site_name))
    contact_email = _metadata_value(metadata, "contactEmail", "contact_email", default=f"privacy@{domain.replace('https://', '').replace('http://', '').strip('/')}")
    effective_date = _metadata_value(metadata, "effectiveDate", "effective_date", default=date.today().strftime("%B %d, %Y"))
    business_type = _metadata_value(metadata, "businessType", "business_type", default="content and recipe blog")
    country = _metadata_value(metadata, "country", default="United States")
    company_name = _metadata_value(metadata, "companyName", "company_name", default=site_name)
    data_controller_name = _metadata_value(metadata, "dataControllerName", "data_controller_name", default=company_name)
    data_controller_email = _metadata_value(metadata, "dataControllerEmail", "data_controller_email", default=contact_email)
    dpo_email = _metadata_value(metadata, "dpoEmail", "dpo_email", default="")
    has_dpo = _yes(metadata.get("hasDPO", metadata.get("has_dpo")), bool(dpo_email))
    gdpr, ccpa = _privacy_regions(country)
    config = {
        "site_name": site_name,
        "domain": domain,
        "contact_email": contact_email,
        "effective_date": effective_date,
        "business_type": business_type,
        "country": country,
        "company_name": company_name,
        "data_controller_name": data_controller_name,
        "data_controller_email": data_controller_email,
        "has_dpo": has_dpo,
        "dpo_email": dpo_email,
        "collects_names": _yes(metadata.get("collectsNames", metadata.get("collects_names")), True),
        "collects_emails": _yes(metadata.get("collectsEmails", metadata.get("collects_emails")), True),
        "collects_ip_addresses": _yes(metadata.get("collectsIPAddresses", metadata.get("collects_ip_addresses")), True),
        "uses_cookies": _yes(metadata.get("usesCookies", metadata.get("uses_cookies")), True),
        "uses_analytics": _yes(metadata.get("usesAnalytics", metadata.get("uses_analytics")), True),
        "uses_newsletter": _yes(metadata.get("usesNewsletter", metadata.get("uses_newsletter")), True),
        "uses_contact_forms": _yes(metadata.get("usesContactForms", metadata.get("uses_contact_forms")), True),
        "allows_comments": _yes(metadata.get("allowsComments", metadata.get("allows_comments")), True),
        "has_user_accounts": _yes(metadata.get("hasUserAccounts", metadata.get("has_user_accounts")), False),
        "uses_ads": _yes(metadata.get("usesAds", metadata.get("uses_ads")), False),
        "uses_affiliate_links": _yes(metadata.get("usesAffiliateLinks", metadata.get("uses_affiliate_links")), False),
        "legal_basis_consent": _yes(metadata.get("legalBasisConsent", metadata.get("legal_basis_consent")), True),
        "legal_basis_legitimate_interest": _yes(metadata.get("legalBasisLegitimateInterest", metadata.get("legal_basis_legitimate_interest")), True),
        "legal_basis_contract": _yes(metadata.get("legalBasisContract", metadata.get("legal_basis_contract")), False),
        "legal_basis_legal_obligation": _yes(metadata.get("legalBasisLegalObligation", metadata.get("legal_basis_legal_obligation")), True),
        "stores_data_in_eu": _yes(metadata.get("storesDataInEU", metadata.get("stores_data_in_eu")), True),
        "uses_third_party_processors": _yes(metadata.get("usesThirdPartyProcessors", metadata.get("uses_third_party_processors")), True),
        "gdpr": gdpr,
        "ccpa": ccpa,
    }
    s = {key: escape(str(value)) for key, value in config.items()}

    items_collected = []
    if config["collects_names"]:
        items_collected.append("Names or display names that you provide when submitting a contact form, leaving a comment, creating an account, subscribing, or otherwise communicating with us.")
    if config["collects_emails"]:
        items_collected.append("Email addresses that you provide for contact requests, newsletter subscriptions, comment notifications, account access, or other requested communications.")
    if config["collects_ip_addresses"]:
        items_collected.append("IP addresses, browser type, device type, operating system, referring pages, pages visited, approximate location derived from technical logs, and similar security or diagnostic information.")
    if config["uses_cookies"]:
        items_collected.append("Cookie identifiers and similar technologies used to remember preferences, understand site usage, and support core website functionality.")
    if config["uses_contact_forms"]:
        items_collected.append("Contact form content, including the message, subject, submitted contact details, and any information you choose to include in your request.")
    if config["allows_comments"]:
        items_collected.append("Comment content and related metadata, such as display name, email address, website URL if provided, IP address, browser user agent, timestamps, and anti-spam signals.")
    if config["has_user_accounts"]:
        items_collected.append("Account and profile information, such as login details, profile settings, preferences, saved content, and account activity.")
    if config["uses_newsletter"]:
        items_collected.append("Newsletter subscription status, email preferences, consent records, unsubscribe requests, and engagement information such as opens or clicks where measured by the email tool.")
    if not items_collected:
        items_collected.append("Only limited technical information necessary to deliver the website, maintain security, and comply with legal obligations.")

    use_purposes = ["operate, maintain, and display the website and its content"]
    if config["uses_cookies"] or config["has_user_accounts"]:
        use_purposes.append("remember preferences and personalize the website experience")
    if config["uses_analytics"]:
        use_purposes.append("measure readership, understand site performance, and improve content through analytics")
    if config["uses_newsletter"]:
        use_purposes.append("send newsletters, updates, and subscription communications you requested")
    if config["uses_contact_forms"]:
        use_purposes.append("respond to messages, provide customer support, and manage inquiries")
    if config["has_user_accounts"]:
        use_purposes.append("create, authenticate, administer, and protect user accounts")
    if config["collects_ip_addresses"] or config["allows_comments"]:
        use_purposes.append("monitor security, prevent fraud, detect spam, and protect the website from abuse")
    if config["uses_ads"]:
        use_purposes.append("display, measure, and improve advertising where enabled")
    if config["uses_affiliate_links"]:
        use_purposes.append("track affiliate referrals and commission attribution through partner links")
    use_purposes.append("comply with applicable laws, enforce policies, and protect legal rights")

    legal_bases = []
    if config["legal_basis_consent"]:
        legal_bases.append("Consent: we may rely on consent for optional cookies, analytics where consent is required, newsletter subscriptions, and other optional processing. You may withdraw consent at any time.")
    if config["legal_basis_legitimate_interest"]:
        legal_bases.append("Legitimate interests: we may process data to operate and secure the website, respond to non-marketing inquiries, prevent abuse, understand content performance, and improve our services, provided those interests are not overridden by your rights and freedoms.")
    if config["legal_basis_contract"]:
        legal_bases.append("Contractual necessity: where accounts, requested services, downloads, memberships, or similar features are provided, we may process data that is necessary to provide those services or take steps at your request before entering into them.")
    if config["legal_basis_legal_obligation"]:
        legal_bases.append("Legal obligation: we may process or retain data when necessary to comply with applicable law, regulatory requests, tax or accounting duties, legal claims, or lawful record-keeping obligations.")
    if not legal_bases:
        legal_bases.append("We process personal data only where a valid legal basis applies under GDPR, such as consent, legitimate interests, contractual necessity, or legal obligations, depending on the feature and context.")

    processor_items = []
    if config["uses_analytics"]:
        processor_items.append("analytics providers that help us measure traffic and content performance")
    if config["uses_newsletter"]:
        processor_items.append("email marketing or newsletter tools used to manage subscriptions and send messages")
    processor_items.append("hosting, infrastructure, security, backup, and technical service providers")
    if config["uses_ads"]:
        processor_items.append("advertising platforms and measurement providers where advertising is enabled")
    if config["uses_affiliate_links"]:
        processor_items.append("affiliate networks or partners that track referral clicks and commission attribution")

    dpo_line = (
        f'<p>Data Protection Officer contact: <a href="mailto:{s["dpo_email"]}">{s["dpo_email"]}</a>.</p>'
        if config["has_dpo"] and config["dpo_email"]
        else ""
    )

    sections = f"""
      <section>
        <h2>Introduction</h2>
        <p>This Privacy Policy explains how {s["company_name"]} ("we", "us", or "our") collects, uses, stores, discloses, and protects personal data when you visit {s["site_name"]} at {s["domain"]}. This policy applies to our {s["business_type"]} website and related online content.</p>
        <p>For GDPR purposes, the data controller is {s["data_controller_name"]}. You can contact the controller at <a href="mailto:{s["data_controller_email"]}">{s["data_controller_email"]}</a>.</p>
      </section>
      <section>
        <h2>Information We Collect</h2>
        <p>Depending on how you use {s["site_name"]}, we may collect the following categories of information:</p>
        <ul>{_list(items_collected)}</ul>
        <p>We do not intentionally collect special category data under GDPR, such as precise health information, biometric data, government identification numbers, or financial account credentials through this website.</p>
      </section>
      <section>
        <h2>How We Use Data</h2>
        <p>We use personal data only for relevant and proportionate purposes, including to:</p>
        <ul>{_list(use_purposes)}</ul>
      </section>
      <section>
        <h2>Legal Basis for Processing</h2>
        <p>Where GDPR or UK GDPR applies, we process personal data using one or more of the following legal bases:</p>
        <ul>{_list(legal_bases)}</ul>
      </section>
      <section>
        <h2>GDPR Rights</h2>
        <p>If GDPR or UK GDPR applies to you, you may exercise the following rights, subject to legal limits and verification where required:</p>
        <ul>{_list([
            "Right of access: request a copy of the personal data we hold about you.",
            "Right to rectification: ask us to correct inaccurate or incomplete personal data.",
            "Right to erasure: ask us to delete personal data where there is no longer a lawful reason to keep it.",
            "Right to restrict processing: ask us to limit how we process your personal data in certain circumstances.",
            "Right to object: object to processing based on legitimate interests or to direct marketing.",
            "Right to data portability: request personal data you provided in a structured, commonly used, machine-readable format where applicable.",
            "Right to withdraw consent: withdraw consent at any time where processing is based on consent, without affecting processing carried out before withdrawal.",
            "Right to lodge a complaint: complain to your local data protection supervisory authority if you believe your rights have been infringed.",
        ])}</ul>
        <p>To exercise a right, contact us at <a href="mailto:{s["data_controller_email"]}">{s["data_controller_email"]}</a>. We may ask for information needed to verify your identity and process the request.</p>
      </section>
      <section>
        <h2>Data Retention</h2>
        <p>We keep personal data only for as long as necessary for the purposes described in this Privacy Policy, including to provide requested services, maintain business and security records, resolve disputes, comply with legal obligations, and enforce our agreements.</p>
        <p>Contact form and support messages are retained for a reasonable period needed to handle the request and maintain records. Newsletter data is retained until you unsubscribe or ask us to delete it, subject to suppression records needed to respect opt-out choices. Security logs and analytics records are retained for limited operational periods unless longer retention is required for security, fraud prevention, or legal reasons.</p>
      </section>
      <section>
        <h2>Security</h2>
        <p>We use appropriate technical and organizational measures designed to protect personal data against unauthorized access, disclosure, alteration, loss, or misuse. These measures may include access controls, secure hosting, encryption in transit where supported, backups, monitoring, and limiting access to people or providers with a legitimate need.</p>
        <p>No website, transmission, or storage system can be guaranteed to be completely secure. If we become aware of a personal data breach requiring notification, we will take steps required by applicable data protection law.</p>
      </section>
    """
    if config["uses_third_party_processors"]:
        sections += f"""
      <section>
        <h2>Third-Party Processors</h2>
        <p>We may use trusted third-party processors to help operate {s["site_name"]}. These providers process personal data on our behalf and are expected to use it only as instructed, subject to suitable confidentiality, security, and data processing terms where required.</p>
        <p>Processors may include:</p>
        <ul>{_list(processor_items)}</ul>
      </section>
        """
    if not config["stores_data_in_eu"]:
        sections += f"""
      <section>
        <h2>International Data Transfers</h2>
        <p>Personal data may be processed or stored outside the European Economic Area, the United Kingdom, or your country of residence. Where required, we use appropriate safeguards for international transfers, such as adequacy decisions, standard contractual clauses, data processing agreements, supplementary security measures, or another lawful transfer mechanism under applicable data protection law.</p>
      </section>
        """
    if config["uses_cookies"]:
        sections += f"""
      <section>
        <h2>Cookies and Similar Technologies</h2>
        <p>We use cookies and similar technologies to operate the website, remember preferences, support security, measure performance, and, where enabled, support analytics, advertising, or affiliate tracking. Non-essential cookies are used only where legally permitted and, where required, based on your consent.</p>
        <p>You can manage cookies through your browser settings and, where available, through our cookie consent tools. Blocking some cookies may affect website features or prevent certain preferences from being saved.</p>
      </section>
        """
    sections += f"""
      <section>
        <h2>Data Sharing and Disclosure</h2>
        <p>We do not sell personal data in the ordinary meaning of the word. We may disclose personal data to service providers, professional advisers, authorities, or other parties when necessary to operate the website, provide requested features, comply with law, protect rights and safety, prevent abuse, or handle a business transfer such as a merger, acquisition, or asset sale.</p>
      </section>
      <section>
        <h2>Children's Privacy</h2>
        <p>{s["site_name"]} is intended for a general audience and is not directed to children under 13. We do not knowingly collect personal data from children under 13. If you believe a child has provided personal data, contact us and we will take appropriate steps to delete it.</p>
      </section>
    """
    if config["ccpa"]:
        sections += f"""
      <section>
        <h2>California, CCPA-Style, and U.S. State Privacy Rights</h2>
        <p>If you are a California resident or live in a U.S. state with applicable privacy laws, you may have the right to know what categories of personal information we collect, request access to or deletion of certain information, correct inaccurate information, opt out of certain sharing or targeted advertising where applicable, and not be discriminated against for exercising your rights.</p>
        <p>To submit a privacy request, contact us at <a href="mailto:{s["data_controller_email"]}">{s["data_controller_email"]}</a>. We may need to verify your request before responding.</p>
      </section>
        """
    sections += f"""
      <section>
        <h2>Policy Changes</h2>
        <p>We may update this Privacy Policy from time to time. The updated version will be posted on this page with a revised effective date. Your continued use of {s["site_name"]} after changes are posted means you accept the updated policy.</p>
      </section>
      <section>
        <h2>Contact and Data Controller</h2>
        <p>Website: {s["domain"]}</p>
        <p>Data controller: {s["data_controller_name"]}</p>
        <p>Controller email: <a href="mailto:{s["data_controller_email"]}">{s["data_controller_email"]}</a></p>
        <p>General privacy contact: <a href="mailto:{s["contact_email"]}">{s["contact_email"]}</a></p>
        {dpo_line}
      </section>
    """
    return config, sections


def generate_privacy_policy_page(metadata: dict) -> str:
    config, sections = _privacy_policy_sections(metadata)
    s = {key: escape(str(value)) for key, value in config.items()}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Privacy Policy | {s["site_name"]}</title>
  <meta name="description" content="Privacy Policy for {s["site_name"]}, including information collection, cookies, analytics, user rights, data sharing, and contact details.">
  <style>
    :root {{ --ink:#071611; --muted:#606b66; --line:#e9e2d8; --paper:#fffdfa; --gold:#f2a600; --green:#1b7a53; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, "Times New Roman", serif; color:var(--ink); background:#fff; line-height:1.7; }}
    a {{ color:var(--green); }}
    .policy-wrap {{ max-width:920px; margin:0 auto; padding:56px 24px 82px; }}
    .policy-kicker {{ margin:0; color:var(--gold); font-size:.82rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }}
    h1 {{ margin:12px 0 10px; font-size:clamp(2.4rem, 5vw, 3.5rem); line-height:1; }}
    .policy-meta {{ margin:0 0 34px; color:var(--muted); }}
    section {{ padding:30px 0; border-top:1px solid var(--line); }}
    h2 {{ position:relative; margin:0 0 18px; padding-bottom:14px; font-size:1.6rem; line-height:1.1; }}
    h2::after {{ position:absolute; left:0; bottom:0; width:48px; height:2px; content:""; background:var(--gold); }}
    p {{ margin:0 0 14px; color:#3f4944; font-size:1.06rem; }}
    ul {{ margin:0; padding-left:24px; color:#3f4944; }}
    li {{ margin:8px 0; }}
    .contact-box {{ margin-top:22px; padding:18px 20px; border:1px solid var(--line); border-radius:8px; background:var(--paper); }}
    @media (max-width: 640px) {{ .policy-wrap {{ padding:38px 18px 62px; }} }}
  </style>
</head>
<body>
  <main class="policy-wrap">
    <p class="policy-kicker">{s["site_name"]}</p>
    <h1>Privacy Policy</h1>
    <p class="policy-meta">Effective date: {s["effective_date"]} &middot; Website: {s["domain"]} &middot; Controller: {s["data_controller_name"]}</p>
    {sections}
    <div class="contact-box">Data controller contact: <a href="mailto:{s["data_controller_email"]}">{s["data_controller_email"]}</a></div>
  </main>
</body>
</html>
"""


def _minimum_age(value) -> int:
    try:
        age = int(value)
    except (TypeError, ValueError):
        return 13
    return max(1, min(age, 120))


def _terms_of_service_sections(metadata: dict) -> tuple[dict, str]:
    site_name = _metadata_value(metadata, "siteName", "site_name", "website_name", default="Website")
    domain = _metadata_value(metadata, "domain", "base_url", default=slugify(site_name))
    contact_email = _metadata_value(metadata, "contactEmail", "contact_email", default=f"legal@{domain.replace('https://', '').replace('http://', '').strip('/')}")
    effective_date = _metadata_value(metadata, "effectiveDate", "effective_date", default=date.today().strftime("%B %d, %Y"))
    country = _metadata_value(metadata, "country", default="United States")
    business_type = _metadata_value(metadata, "businessType", "business_type", default="content and informational website")
    company_name = _metadata_value(metadata, "companyName", "company_name", default=site_name)
    is_eu, is_us, is_uk = _jurisdiction_flags(country)
    config = {
        "site_name": site_name,
        "domain": domain,
        "contact_email": contact_email,
        "effective_date": effective_date,
        "country": country,
        "business_type": business_type,
        "company_name": company_name,
        "allows_comments": _yes(metadata.get("allowsComments", metadata.get("allows_comments")), True),
        "allows_user_content": _yes(metadata.get("allowsUserContent", metadata.get("allows_user_content")), False),
        "uses_affiliate_links": _yes(metadata.get("usesAffiliateLinks", metadata.get("uses_affiliate_links")), False),
        "uses_ads": _yes(metadata.get("usesAds", metadata.get("uses_ads")), False),
        "has_user_accounts": _yes(metadata.get("hasUserAccounts", metadata.get("has_user_accounts")), False),
        "sells_products": _yes(metadata.get("sellsProducts", metadata.get("sells_products")), False),
        "minimum_age": _minimum_age(metadata.get("minimumAge", metadata.get("minimum_age", 13))),
        "is_eu": is_eu,
        "is_us": is_us,
        "is_uk": is_uk,
    }
    s = {key: escape(str(value)) for key, value in config.items()}
    sections = f"""
      <section>
        <h2>Introduction and Acceptance of Terms</h2>
        <p>These Terms of Service ("Terms") govern your access to and use of {s["site_name"]} at {s["domain"]}. {s["site_name"]} is operated by {s["company_name"]} as a {s["business_type"]}.</p>
        <p>By accessing or using the website, you agree to be bound by these Terms. If you do not agree, you must not use the website.</p>
      </section>
      <section>
        <h2>Eligibility and Minimum Age</h2>
        <p>You must be at least {s["minimum_age"]} years old to use this website. If you are under the age of majority in your location, you may use the website only with the involvement and consent of a parent or legal guardian.</p>
      </section>
      <section>
        <h2>Website Use Rules</h2>
        <p>You may use {s["site_name"]} for lawful, personal, informational, and non-commercial purposes. You agree to use the website in a manner that respects our content, our systems, other visitors, and applicable laws.</p>
      </section>
      <section>
        <h2>Prohibited Activities</h2>
        <p>You agree not to misuse the website. Prohibited activities include attempting to interfere with website security, scraping content without permission, uploading malware, impersonating others, submitting unlawful or misleading content, infringing intellectual property rights, or using the website for spam, harassment, fraud, or other harmful conduct.</p>
      </section>
      <section>
        <h2>Intellectual Property</h2>
        <p>Unless otherwise stated, the content on {s["site_name"]}, including articles, recipes, text, graphics, branding, design elements, and other materials, is owned by or licensed to {s["company_name"]}. You may not copy, reproduce, republish, sell, or exploit our content without prior written permission, except as permitted by law or for personal use.</p>
      </section>
    """
    if config["allows_comments"]:
        sections += f"""
      <section>
        <h2>Comments and Community Rules</h2>
        <p>If comments are available, you are responsible for what you submit. Comments must be respectful, accurate, lawful, and relevant. We may moderate, edit, refuse, or remove comments that are abusive, promotional, misleading, infringing, unlawful, or otherwise inappropriate. Publication of a comment does not mean we endorse it.</p>
      </section>
        """
    if config["allows_user_content"]:
        sections += f"""
      <section>
        <h2>User-Generated Content</h2>
        <p>If you submit content such as comments, reviews, photos, tips, or other materials, you retain ownership of your content but grant {s["company_name"]} a non-exclusive, worldwide, royalty-free license to use, display, reproduce, modify, distribute, and publish that content in connection with operating, promoting, and improving {s["site_name"]}. You represent that you have the rights needed to submit the content and that it does not violate the rights of others.</p>
      </section>
        """
    if config["uses_affiliate_links"]:
        sections += f"""
      <section>
        <h2>Affiliate Links and Third-Party Responsibility</h2>
        <p>{s["site_name"]} may include affiliate links. If you click an affiliate link or purchase through a partner, we may earn a commission at no extra cost to you. Third-party sites, products, services, pricing, availability, claims, and policies are controlled by those third parties, not by us.</p>
      </section>
        """
    if config["uses_ads"]:
        sections += f"""
      <section>
        <h2>Advertising</h2>
        <p>The website may display advertising from third-party ad networks or sponsors. Advertisements do not necessarily reflect our views or recommendations. We are not responsible for the content, accuracy, privacy practices, or offers made by advertisers or advertising networks.</p>
      </section>
        """
    if config["has_user_accounts"]:
        sections += f"""
      <section>
        <h2>User Accounts</h2>
        <p>If account features are offered, you are responsible for maintaining the confidentiality of your login credentials and for all activity under your account. You agree to provide accurate information, keep it updated, and notify us promptly of unauthorized access. We may suspend or terminate accounts that violate these Terms, create risk, or misuse the website.</p>
      </section>
        """
    if config["sells_products"]:
        sections += f"""
      <section>
        <h2>Purchases, Payments, and Refunds</h2>
        <p>If products, digital downloads, memberships, or services are offered through {s["site_name"]}, prices, availability, payment terms, delivery terms, and refund policies may be described at checkout or on product pages. You agree to provide accurate purchase information and authorize applicable charges. Unless a separate refund policy states otherwise, purchases may be final to the fullest extent permitted by law.</p>
      </section>
        """
    sections += f"""
      <section>
        <h2>Third-Party Services and Links</h2>
        <p>{s["site_name"]} may link to third-party websites, tools, platforms, products, or services. We do not control and are not responsible for third-party content, policies, practices, or availability. Your use of third-party services is at your own risk and may be governed by their separate terms.</p>
      </section>
      <section>
        <h2>Disclaimer of Warranties</h2>
        <p>The website and its content are provided for general informational purposes on an "as is" and "as available" basis. We do not guarantee that the website will be uninterrupted, error-free, secure, or that content will always be accurate, complete, current, or suitable for your specific circumstances.</p>
      </section>
      <section>
        <h2>Limitation of Liability</h2>
        <p>To the fullest extent permitted by applicable law, {s["company_name"]} and its owners, contributors, partners, and service providers will not be liable for indirect, incidental, consequential, special, punitive, or exemplary damages arising from or related to your use of the website or reliance on its content.</p>
      </section>
      <section>
        <h2>Termination</h2>
        <p>We may suspend, restrict, or terminate access to all or part of the website at any time if we believe a user has violated these Terms, created legal risk, harmed other users, or interfered with website operation. You may stop using the website at any time.</p>
      </section>
      <section>
        <h2>Governing Law</h2>
        <p>These Terms are governed by the laws of {s["country"]}, without regard to conflict-of-law principles, unless mandatory consumer protection laws in your location require otherwise.</p>
      </section>
    """
    if config["is_eu"]:
        sections += f"""
      <section>
        <h2>EU Consumer and Mandatory Rights</h2>
        <p>If you are located in the European Union, nothing in these Terms limits mandatory consumer rights or protections that cannot be excluded under applicable law. Where required, disputes may be handled in the courts or forums available under applicable EU consumer protection rules.</p>
      </section>
        """
    if config["is_us"]:
        sections += f"""
      <section>
        <h2>United States Legal Notice</h2>
        <p>If you access the website from the United States, you agree that these Terms are intended to be interpreted to the maximum extent permitted by applicable U.S. law. Some states do not allow certain warranty exclusions or liability limitations, so portions of those sections may not apply to you.</p>
      </section>
        """
    if config["is_uk"]:
        sections += f"""
      <section>
        <h2>UK Legal Notice</h2>
        <p>If you are located in the United Kingdom, these Terms do not limit legal rights that cannot be excluded under UK law, including rights relating to unfair contract terms, consumer protection, or liability for fraud, fraudulent misrepresentation, death, or personal injury caused by negligence.</p>
      </section>
        """
    sections += f"""
      <section>
        <h2>Changes to These Terms</h2>
        <p>We may update these Terms from time to time. Updated Terms will be posted on this page with a revised effective date. Your continued use of {s["site_name"]} after changes are posted means you accept the updated Terms.</p>
      </section>
      <section>
        <h2>Contact Information</h2>
        <p>If you have questions about these Terms, contact us at <a href="mailto:{s["contact_email"]}">{s["contact_email"]}</a>.</p>
      </section>
    """
    return config, sections


def generate_terms_of_service_page(metadata: dict) -> str:
    config, sections = _terms_of_service_sections(metadata)
    s = {key: escape(str(value)) for key, value in config.items()}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Terms of Service | {s["site_name"]}</title>
  <meta name="description" content="Terms of Service for {s["site_name"]}, including website use rules, intellectual property, third-party services, disclaimers, liability, governing law, and contact information.">
  <style>
    :root {{ --ink:#071611; --muted:#606b66; --line:#e9e2d8; --paper:#fffdfa; --gold:#f2a600; --green:#1b7a53; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, "Times New Roman", serif; color:var(--ink); background:#fff; line-height:1.7; }}
    a {{ color:var(--green); }}
    .terms-wrap {{ max-width:920px; margin:0 auto; padding:56px 24px 82px; }}
    .terms-kicker {{ margin:0; color:var(--gold); font-size:.82rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }}
    h1 {{ margin:12px 0 10px; font-size:clamp(2.4rem, 5vw, 3.5rem); line-height:1; }}
    .terms-meta {{ margin:0 0 34px; color:var(--muted); }}
    section {{ padding:30px 0; border-top:1px solid var(--line); }}
    h2 {{ position:relative; margin:0 0 18px; padding-bottom:14px; font-size:1.6rem; line-height:1.1; }}
    h2::after {{ position:absolute; left:0; bottom:0; width:48px; height:2px; content:""; background:var(--gold); }}
    p {{ margin:0 0 14px; color:#3f4944; font-size:1.06rem; }}
    .contact-box {{ margin-top:22px; padding:18px 20px; border:1px solid var(--line); border-radius:8px; background:var(--paper); }}
    @media (max-width: 640px) {{ .terms-wrap {{ padding:38px 18px 62px; }} }}
  </style>
</head>
<body>
  <main class="terms-wrap">
    <p class="terms-kicker">{s["site_name"]}</p>
    <h1>Terms of Service</h1>
    <p class="terms-meta">Effective date: {s["effective_date"]} &middot; Website: {s["domain"]} &middot; Jurisdiction: {s["country"]}</p>
    {sections}
    <div class="contact-box">Terms contact: <a href="mailto:{s["contact_email"]}">{s["contact_email"]}</a></div>
  </main>
</body>
</html>
"""


def _normalise_niche(value: str) -> str:
    niche = (value or "").strip().lower()
    allowed = {
        "recipes",
        "health",
        "fitness",
        "finance",
        "technology",
        "travel",
        "education",
        "general blog",
        "product reviews",
        "business",
    }
    return niche if niche in allowed else "general blog"


def _disclaimer_sections(metadata: dict) -> tuple[dict, str]:
    site_name = _metadata_value(metadata, "siteName", "site_name", "website_name", default="Website")
    domain = _metadata_value(metadata, "domain", "base_url", default=slugify(site_name))
    contact_email = _metadata_value(metadata, "contactEmail", "contact_email", default=f"hello@{domain.replace('https://', '').replace('http://', '').strip('/')}")
    effective_date = _metadata_value(metadata, "effectiveDate", "effective_date", default=date.today().strftime("%B %d, %Y"))
    country = _metadata_value(metadata, "country", default="United States")
    business_type = _metadata_value(metadata, "businessType", "business_type", default="informational website")
    company_name = _metadata_value(metadata, "companyName", "company_name", default=site_name)
    affiliate_programs = _string_list(metadata.get("affiliatePrograms", metadata.get("affiliate_programs")))
    affiliate_program_names = ", ".join(affiliate_programs)
    has_amazon = any("amazon" in program.lower() for program in affiliate_programs)
    non_amazon_programs = [program for program in affiliate_programs if "amazon" not in program.lower()]
    niche_type = _normalise_niche(_metadata_value(metadata, "nicheType", "niche_type", default="general blog"))
    config = {
        "site_name": site_name,
        "domain": domain,
        "contact_email": contact_email,
        "effective_date": effective_date,
        "country": country,
        "business_type": business_type,
        "company_name": company_name,
        "niche_type": niche_type,
        "uses_affiliate_links": _yes(metadata.get("usesAffiliateLinks", metadata.get("uses_affiliate_links")), False),
        "affiliate_programs": affiliate_program_names,
        "has_amazon": has_amazon,
        "has_other_affiliate_programs": bool(non_amazon_programs),
        "uses_ads": _yes(metadata.get("usesAds", metadata.get("uses_ads")), False),
        "links_to_third_party_sites": _yes(metadata.get("linksToThirdPartySites", metadata.get("links_to_third_party_sites")), True),
        "displays_health_info": _yes(metadata.get("displaysHealthInfo", metadata.get("displays_health_info")), niche_type in {"health", "fitness"}),
        "displays_nutrition_info": _yes(metadata.get("displaysNutritionInfo", metadata.get("displays_nutrition_info")), niche_type == "recipes"),
        "displays_financial_info": _yes(metadata.get("displaysFinancialInfo", metadata.get("displays_financial_info")), niche_type == "finance"),
        "displays_legal_info": _yes(metadata.get("displaysLegalInfo", metadata.get("displays_legal_info")), False),
        "displays_tech_advice": _yes(metadata.get("displaysTechAdvice", metadata.get("displays_tech_advice")), niche_type == "technology"),
        "allows_user_generated_content": _yes(metadata.get("allowsUserGeneratedContent", metadata.get("allows_user_generated_content", metadata.get("allowsUserContent", metadata.get("allows_user_content")))), False),
        "publishes_product_reviews": _yes(metadata.get("publishesProductReviews", metadata.get("publishes_product_reviews")), niche_type == "product reviews"),
        "sells_products": _yes(metadata.get("sellsProducts", metadata.get("sells_products")), False),
    }
    s = {key: escape(str(value)) for key, value in config.items()}
    sections = f"""
      <section>
        <h2>General Information Disclaimer</h2>
        <p>The information provided by {s["company_name"]} on {s["site_name"]} at {s["domain"]} is for general informational and educational purposes only. The content is published in good faith for readers interested in our {s["business_type"]} content and should not be treated as professional, individualized, or legally binding advice.</p>
        <p>Your use of {s["site_name"]} and reliance on any information on this website is solely at your own risk.</p>
      </section>
      <section>
        <h2>Accuracy and No Warranty</h2>
        <p>We aim to keep the information on {s["site_name"]} accurate, current, and useful, but we make no representations or warranties of any kind, express or implied, about completeness, accuracy, reliability, suitability, availability, or results from using the website or its content.</p>
        <p>Content may contain errors, omissions, outdated details, or typographical mistakes. We may update, change, or remove content at any time without notice.</p>
      </section>
      <section>
        <h2>Limitation of Liability</h2>
        <p>To the fullest extent permitted by applicable law, {s["company_name"]}, its owners, contributors, partners, employees, service providers, and affiliates will not be liable for any loss, damage, injury, claim, cost, or expense arising from your use of, or inability to use, {s["site_name"]} or your reliance on any information provided on the website.</p>
        <p>This includes direct, indirect, incidental, consequential, special, punitive, or similar damages, even if we have been advised of the possibility of such damages.</p>
      </section>
      <section>
        <h2>External Links Disclaimer</h2>
        <p>{s["site_name"]} may contain links to external websites, tools, platforms, products, or services that are not owned or controlled by us. External links are provided for convenience and informational purposes only.</p>
        <p>We do not guarantee and are not responsible for the accuracy, availability, security, content, policies, practices, or offerings of third-party websites or services.</p>
      </section>
    """
    if config["uses_affiliate_links"]:
        sections += f"""
      <section>
        <h2>Affiliate Disclosure</h2>
        <p>{s["site_name"]} may include affiliate links. If you click an affiliate link and make a purchase or take another qualifying action, we may earn a commission at no additional cost to you.</p>
        <p>Affiliate relationships do not control our editorial content. We aim to recommend products, services, or resources only when we believe they may be relevant or useful to readers.</p>
      </section>
        """
        if config["has_amazon"]:
            sections += f"""
      <section>
        <h2>Amazon Associates Disclosure</h2>
        <p>{s["site_name"]} participates in the Amazon Associates Program. As an Amazon Associate, we earn from qualifying purchases.</p>
      </section>
            """
        if config["has_other_affiliate_programs"]:
            programs = escape(", ".join(non_amazon_programs))
            sections += f"""
      <section>
        <h2>Other Affiliate Programs</h2>
        <p>We may also participate in affiliate programs including {programs}. These programs may use tracking links or referral identifiers to attribute purchases or sign-ups to {s["site_name"]}.</p>
      </section>
            """
    if config["uses_ads"]:
        sections += f"""
      <section>
        <h2>Advertising Disclaimer</h2>
        <p>{s["site_name"]} may display advertisements from third-party advertising networks, sponsors, or direct partners. Advertisements may be selected or personalized by those providers based on their own technologies, policies, and data practices.</p>
        <p>The appearance of an advertisement does not mean we endorse the advertiser, product, service, claim, or offer.</p>
      </section>
        """
    if config["links_to_third_party_sites"]:
        sections += f"""
      <section>
        <h2>Third-Party Responsibility</h2>
        <p>When you leave {s["site_name"]} through a third-party link, you are responsible for reviewing that third party's terms, privacy policy, refund policy, product information, and safety practices. We are not responsible for transactions, communications, downloads, claims, or disputes involving third-party sites or services.</p>
      </section>
        """
    if config["allows_user_generated_content"]:
        sections += f"""
      <section>
        <h2>User-Generated Content Disclaimer</h2>
        <p>{s["site_name"]} may allow users to submit comments, reviews, messages, images, tips, or other content. User-submitted content reflects the views and responsibility of the person who submitted it and does not necessarily reflect our views.</p>
        <p>We may moderate, edit, remove, or refuse user content, but we do not guarantee that all user content is reviewed before publication.</p>
      </section>
        """
    if config["publishes_product_reviews"]:
        sections += f"""
      <section>
        <h2>Product Reviews and Opinions</h2>
        <p>Product reviews, comparisons, recommendations, ratings, and opinions on {s["site_name"]} are based on our editorial judgment, available information, personal experience, research, or contributor perspectives at the time of publication.</p>
        <p>Individual experiences may vary. You should verify specifications, pricing, availability, warranties, and suitability directly with the seller, manufacturer, or service provider before purchasing.</p>
      </section>
        """
    if config["sells_products"]:
        sections += f"""
      <section>
        <h2>Products, Purchases, and E-Commerce</h2>
        <p>If {s["site_name"]} sells products, digital items, memberships, downloads, or services, product descriptions, pricing, availability, delivery times, and results may change without notice. We do not guarantee that every product or service will meet your expectations or be suitable for every use case.</p>
        <p>To the fullest extent permitted by law, our liability for purchases is limited to the amount paid for the product or service giving rise to the claim, unless a separate written policy states otherwise.</p>
      </section>
        """

    if niche_type == "recipes":
        sections += f"""
      <section>
        <h2>Recipe, Nutrition, Allergy, and Dietary Disclaimer</h2>
        <p>Recipes, cooking tips, meal ideas, and nutrition information on {s["site_name"]} are provided for general informational purposes only. Nutrition values are estimates and may vary based on brands, ingredient substitutions, portion sizes, preparation methods, and calculation tools.</p>
        <p>You are responsible for checking ingredients, labels, allergens, cross-contamination risks, and dietary suitability before preparing or consuming any recipe. If you have allergies, intolerances, medical dietary restrictions, or specific nutrition needs, consult a qualified professional.</p>
        <p>Recipe results may vary depending on equipment, ingredient quality, altitude, climate, skill level, substitutions, and cooking conditions.</p>
      </section>
        """
    if niche_type == "health" or config["displays_health_info"]:
        sections += f"""
      <section>
        <h2>Health and Medical Disclaimer</h2>
        <p>Health-related content on {s["site_name"]} is for general informational purposes only and is not medical advice. It is not intended to diagnose, treat, cure, or prevent any disease or condition.</p>
        <p>Using this website does not create a doctor-patient, therapist-patient, or other healthcare professional relationship. Always seek advice from a qualified healthcare provider about medical conditions, symptoms, treatment decisions, medications, supplements, or lifestyle changes.</p>
        <p>If you believe you may have a medical emergency, contact emergency services or your local emergency number immediately.</p>
      </section>
        """
    if niche_type == "fitness":
        sections += f"""
      <section>
        <h2>Fitness and Exercise Risk Disclaimer</h2>
        <p>Fitness, exercise, training, and movement content on {s["site_name"]} may involve physical risk. You are responsible for determining whether exercises are appropriate for your health, fitness level, experience, and environment.</p>
        <p>Consult a qualified healthcare professional before starting a new exercise program, especially if you are pregnant, injured, managing a medical condition, taking medication, or returning to activity after a break.</p>
      </section>
        """
    if niche_type == "finance" or config["displays_financial_info"]:
        sections += f"""
      <section>
        <h2>Financial and Investment Disclaimer</h2>
        <p>Financial, business, investment, tax, budgeting, and earnings-related content on {s["site_name"]} is for informational purposes only and is not financial, investment, tax, accounting, or legal advice.</p>
        <p>Using this website does not create a financial advisor-client, fiduciary, accountant-client, or attorney-client relationship. You should consult qualified professionals before making financial, investment, tax, or business decisions.</p>
        <p>Markets, investments, income opportunities, and business outcomes involve risk. Past performance, examples, case studies, or earnings discussions do not guarantee future results.</p>
      </section>
        """
    if niche_type == "technology" or config["displays_tech_advice"]:
        sections += f"""
      <section>
        <h2>Technology and Implementation Disclaimer</h2>
        <p>Technology tutorials, software guidance, automation steps, code examples, tool recommendations, and implementation advice on {s["site_name"]} are provided for general informational purposes only.</p>
        <p>Software, platforms, APIs, pricing, features, and security practices can change. You are responsible for testing, backups, security review, compliance review, and determining whether any implementation is suitable for your systems before using it in production.</p>
      </section>
        """
    if niche_type == "travel":
        sections += f"""
      <section>
        <h2>Travel Information Disclaimer</h2>
        <p>Travel content on {s["site_name"]} may include destination information, schedules, prices, availability, entry rules, safety notes, and recommendations that can change quickly. Always verify important details with official sources, providers, airlines, accommodations, tour operators, or local authorities before making travel decisions.</p>
        <p>We are not responsible for changes in pricing, availability, delays, cancellations, closures, visa rules, weather, safety conditions, or other travel disruptions.</p>
      </section>
        """
    if niche_type == "education":
        sections += f"""
      <section>
        <h2>Educational Disclaimer</h2>
        <p>Educational content on {s["site_name"]} is provided for learning and informational purposes only. We do not guarantee academic, professional, exam, certification, employment, financial, or personal outcomes from using our content.</p>
        <p>You are responsible for verifying requirements with schools, employers, certification bodies, regulators, or other relevant institutions.</p>
      </section>
        """
    if niche_type == "product reviews":
        sections += f"""
      <section>
        <h2>Review Independence</h2>
        <p>Review content on {s["site_name"]} represents opinions and editorial assessments at the time of publication. We aim to keep review content independent, clear, and useful, even when affiliate links, advertising, sponsorships, samples, or partnerships are present.</p>
      </section>
        """
    if config["displays_legal_info"]:
        sections += f"""
      <section>
        <h2>Legal Information Disclaimer</h2>
        <p>Legal or compliance-related content on {s["site_name"]} is provided for general informational purposes only and is not legal advice. Using this website does not create an attorney-client relationship. Consult a qualified lawyer in your jurisdiction for advice about your specific situation.</p>
      </section>
        """
    sections += f"""
      <section>
        <h2>Contact Information</h2>
        <p>If you have questions about this Disclaimer, contact {s["company_name"]} at <a href="mailto:{s["contact_email"]}">{s["contact_email"]}</a>.</p>
        <p>Website: {s["domain"]}</p>
        <p>Country or primary jurisdiction: {s["country"]}</p>
      </section>
    """
    return config, sections


def generate_disclaimer_page(metadata: dict) -> str:
    config, sections = _disclaimer_sections(metadata)
    s = {key: escape(str(value)) for key, value in config.items()}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Disclaimer | {s["site_name"]}</title>
  <meta name="description" content="Disclaimer for {s["site_name"]}, including informational content, accuracy, liability, external links, affiliate disclosures, advertising, and niche-specific notices.">
  <style>
    :root {{ --ink:#071611; --muted:#606b66; --line:#e9e2d8; --paper:#fffdfa; --gold:#f2a600; --green:#1b7a53; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, "Times New Roman", serif; color:var(--ink); background:#fff; line-height:1.7; }}
    a {{ color:var(--green); }}
    .disclaimer-wrap {{ max-width:920px; margin:0 auto; padding:56px 24px 82px; }}
    .disclaimer-kicker {{ margin:0; color:var(--gold); font-size:.82rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }}
    h1 {{ margin:12px 0 10px; font-size:clamp(2.4rem, 5vw, 3.5rem); line-height:1; }}
    .disclaimer-meta {{ margin:0 0 34px; color:var(--muted); }}
    section {{ padding:30px 0; border-top:1px solid var(--line); }}
    h2 {{ position:relative; margin:0 0 18px; padding-bottom:14px; font-size:1.6rem; line-height:1.1; }}
    h2::after {{ position:absolute; left:0; bottom:0; width:48px; height:2px; content:""; background:var(--gold); }}
    p {{ margin:0 0 14px; color:#3f4944; font-size:1.06rem; }}
    .contact-box {{ margin-top:22px; padding:18px 20px; border:1px solid var(--line); border-radius:8px; background:var(--paper); }}
    @media (max-width: 640px) {{ .disclaimer-wrap {{ padding:38px 18px 62px; }} }}
  </style>
</head>
<body>
  <main class="disclaimer-wrap">
    <p class="disclaimer-kicker">{s["site_name"]}</p>
    <h1>Disclaimer</h1>
    <p class="disclaimer-meta">Effective date: {s["effective_date"]} &middot; Website: {s["domain"]} &middot; Niche: {s["niche_type"]}</p>
    {sections}
    <div class="contact-box">Disclaimer contact: <a href="mailto:{s["contact_email"]}">{s["contact_email"]}</a></div>
  </main>
</body>
</html>
"""


def _page_shell(site: dict, title: str, body: str, active: str = "", prefix: str = "", extra_head: str = "") -> str:
    website_name = escape(site["website_name"])
    tagline = escape(site["tagline"])
    has_logo = bool(site.get("logo_image_filename"))
    logo = _asset_img(site.get("logo_image_filename"), site["website_name"], "brand-logo", prefix)
    brand_content = (
        logo
        if has_logo
        else f'<span class="brand-text"><strong>{website_name}</strong><span>{tagline}</span></span>'
    )
    brand_class = "brand logo-only" if has_logo else "brand"
    favicon = (
        f'  <link rel="icon" href="{prefix}assets/{escape(site["favicon_image_filename"])}">\n'
        if site.get("favicon_image_filename")
        else ""
    )
    site_categories = site.get("categories") or ["Breakfast", "Lunch", "Dinner", "Dessert"]
    nav = [(f"{prefix}index.html", "Home", "home")]
    for cat in site_categories[:5]:
        nav.append((f"{prefix}category/{slugify(cat)}/", cat, slugify(cat)))
    nav += [
        (f"{prefix}about.html", "About", "about"),
        (f"{prefix}contact.html", "Contact", "contact"),
    ]
    nav_html = "".join(
        f'<a class="{"active" if key == active else ""}" href="{href}">{escape(label)}</a>'
        for href, label, key in nav
    )

    # Footer categories column
    niche_col_label = {
        "recipes": "Recipes", "health": "Topics", "fitness": "Topics",
        "finance": "Topics", "technology": "Topics",
    }.get((site.get("niche_type") or "").lower(), "Categories")
    cat_footer_links = f'<a href="{prefix}index.html#content">All Posts</a>' + "".join(
        f'<a href="{prefix}category/{slugify(c)}/">{escape(c)}</a>'
        for c in site_categories[:6]
    )

    # Footer social column — only show platforms that have a URL
    social_links: dict = site.get("social_links") or {}
    social_placement: str = site.get("social_placement", "footer_only")

    social_footer_items = "".join(
        f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(SOCIAL_PLATFORM_LABELS.get(platform, platform.title()))}</a>'
        for platform, url in social_links.items() if url
    )
    social_footer_col = (
        f'<div><h3>Follow Us</h3>{social_footer_items}</div>'
        if social_footer_items and social_placement in ("footer_only", "both") else ""
    )

    # Header social icons — controlled by social_placement setting
    header_social = ""
    if social_placement in ("header_only", "both"):
        header_social = "".join(
            f'<a href="{escape(social_links[p])}" target="_blank" rel="noopener noreferrer" aria-label="{escape(SOCIAL_PLATFORM_LABELS.get(p, p))}" style="font-size:1.1rem;text-decoration:none">'
            + {"pinterest": "📌", "instagram": "📷", "facebook": "📘", "twitter": "🐦",
               "tiktok": "🎵", "youtube": "▶", "linkedin": "💼"}[p]
            + "</a>"
            for p in ["pinterest", "instagram", "facebook", "twitter", "tiktok", "youtube", "linkedin"]
            if social_links.get(p)
        )
    header_social_html = (
        f'<div class="header-social" style="display:flex;gap:10px;align-items:center">{header_social}</div>'
        if header_social else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | {website_name}</title>
  <meta name="description" content="{tagline}">
{favicon}  <link rel="stylesheet" href="{prefix}style.css">
{extra_head}</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a class="{brand_class}" href="{prefix}index.html" aria-label="{website_name} home">{brand_content}</a>
      <nav aria-label="Primary navigation">{nav_html}</nav>
      <div style="display:flex;align-items:center;gap:12px">
        {header_social_html}
        <form class="site-search" action="{prefix}index.html#content">
          <label class="sr-only" for="site-search">Search</label>
          <input id="site-search" name="q" type="search" placeholder="Search...">
          <button type="submit" aria-label="Search">&#128269;</button>
        </form>
      </div>
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false">
        <span></span>
        <span></span>
        <span></span>
      </button>
    </div>
  </header>
  <main>{body}</main>
  <footer class="site-footer">
    <div class="footer-about">
      <a class="footer-brand" href="{prefix}index.html">{website_name}</a>
      <p class="footer-kicker">Simple Recipes That Work.</p>
      <p class="footer-desc">Tested recipes for real kitchens. Simple ingredients, clear steps, dependable results.</p>
    </div>
    <div>
      <h3>{escape(niche_col_label)}</h3>
      {cat_footer_links}
    </div>
    {social_footer_col}
    <div>
      <h3>Legal</h3>
      <a href="{prefix}about.html">About Us</a>
      <a href="{prefix}contact.html">Contact</a>
      <a href="{prefix}privacy-policy.html">Privacy Policy</a>
      <a href="{prefix}terms-of-use.html">Terms of Use</a>
      <a href="{prefix}disclaimer.html">Disclaimer</a>
    </div>
  </footer>
  <p class="copyright">&copy; 2026 {website_name}. All rights reserved.</p>
  <script>
    document.addEventListener('DOMContentLoaded', function() {{
      const navToggle = document.querySelector('.nav-toggle');
      const nav = document.querySelector('nav');
      if (navToggle && nav) {{
        navToggle.addEventListener('click', function() {{
          this.classList.toggle('active');
          nav.classList.toggle('active');
          this.setAttribute('aria-expanded', this.classList.contains('active'));
        }});
        // Close menu on link click
        const navLinks = nav.querySelectorAll('a');
        navLinks.forEach(link => {{
          link.addEventListener('click', function() {{
            navToggle.classList.remove('active');
            nav.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
          }});
        }});
        // Close menu on outside click
        document.addEventListener('click', function(e) {{
          if (!e.target.closest('.site-header')) {{
            navToggle.classList.remove('active');
            nav.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
          }}
        }});
      }}
      
      // Fetch and render posts from API
      async function renderPosts() {{
        try {{
          // Extract site slug from current URL
          const pathParts = window.location.pathname.split('/');
          const siteSlug = pathParts[2];
          
          // Find all recipe grids that need content
          const grids = document.querySelectorAll('.recipe-grid[data-category], .recipe-grid[data-section="featured"]');
          
          for (const grid of grids) {{
            const category = grid.getAttribute('data-category');
            const isFeature = grid.hasAttribute('data-section');
            
            try {{
              const url = isFeature 
                ? `/api/v1/sites/${{siteSlug}}/posts?page_size=6`
                : `/api/v1/sites/${{siteSlug}}/posts?category=${{encodeURIComponent(category)}}&page_size=12`;
              
              const response = await fetch(url);
              if (!response.ok) throw new Error('Failed to fetch posts');
              
              const data = await response.json();
              const posts = data.posts || [];
              
              // Update count if on category page
              if (category) {{
                const countEl = document.querySelector('.recipe-count');
                if (countEl) countEl.textContent = posts.length + ' recipes in this category';
              }}
              
              // Render cards
              grid.innerHTML = posts.length > 0
                ? posts.map(post => `
                    <article class="recipe-card">
                      <a href="{prefix}recipe/${{post.slug}}/">
                        <div class="recipe-photo photo-fallback">
                          <span>${{post.category || 'Recipe'}}</span>
                        </div>
                        <div class="recipe-body">
                          <h3>${{post.title}}</h3>
                          <p>${{post.excerpt || post.content.substring(0, 100)}}</p>
                          <div class="recipe-meta">
                            <span>&#9719;&nbsp;Featured</span>
                            <span class="stars" aria-label="5 stars"></span>
                          </div>
                        </div>
                      </a>
                    </article>
                  `).join('')
                : `<p style="grid-column:1/-1;text-align:center;color:#888;padding:40px">No recipes yet. Check back soon!</p>`;
            }} catch (e) {{
              console.error('Error loading posts:', e);
              grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;color:#999">Unable to load recipes</p>';
            }}
          }}
        }} catch (e) {{
          console.error('Error in renderPosts:', e);
        }}
      }}
      
      renderPosts();
    }});
  </script>
</body>
</html>
"""


def _recipe_card(title: str, category: str, minutes: str, rating: str, description: str, prefix: str = "") -> str:
    image_class = f"photo-{slugify(title)}" if title in RECIPE_IMAGES else "photo-fallback"
    href = f"{prefix}recipe/{slugify(title)}/"
    r, count = _article_rating(title)
    return f"""
      <article class="recipe-card">
        <a href="{href}" aria-label="Read {escape(title)}">
          <div class="recipe-photo {image_class}"><span>{escape(category)}</span></div>
          <div class="recipe-body">
            <h3>{escape(title)}</h3>
            <p>{escape(description)}</p>
            <div class="recipe-meta">
              <span>&#9719;&nbsp;{escape(minutes)}</span>
              <span class="stars" aria-label="{r} stars"></span>
            </div>
          </div>
        </a>
      </article>
    """


def _category_section(site: dict, category: str, limit: int = 3) -> str:
    """Return a homepage section for one category — real data if available, placeholder otherwise."""
    cat_id = slugify(category)
    if category in CATEGORY_RECIPES:
        cards = "".join(
            _recipe_card(title, category, minutes, "", desc)
            for title, minutes, desc in CATEGORY_RECIPES[category][:limit]
        )
    else:
        cards = "".join(
            f'<article class="recipe-card"><a href="category/{cat_id}/"><div class="recipe-photo photo-fallback"><span>{escape(category)}</span></div>'
            f'<div class="recipe-body"><h3>{escape(category)} — Coming Soon</h3>'
            f'<p>New posts in this category are on the way.</p></div></a></article>'
            for _ in range(min(limit, 2))
        )
    return f"""
      <section class="recipe-section" id="{cat_id}">
        <div class="section-head"><h2>{escape(category)}</h2><a href="category/{cat_id}/">View All &rarr;</a></div>
        <div class="recipe-grid">{cards}</div>
      </section>"""


def _home(site: dict) -> str:
    chef = escape(site["chef_name"])
    website_name = escape(site["website_name"])
    categories = site.get("categories") or ["Breakfast", "Lunch", "Dinner", "Dessert"]
    site_slug = slugify(website_name)

    # Generate category sections with JS-populated content
    category_sections = "".join(
        f'''<section class="recipe-section" id="{slugify(cat)}">
        <div class="section-head"><h2>{escape(cat)}</h2><a href="category/{slugify(cat)}/">View All &rarr;</a></div>
        <div class="recipe-grid" data-category="{escape(cat)}"></div>
      </section>'''
        for cat in categories[:6]
    )

    chips = "".join(f'<a href="#{slugify(c)}">{escape(c)}</a>' for c in categories)

    body = f"""
      <section class="hero">
        <p class="eyebrow">Welcome to {website_name}</p>
        <h1>{escape(site["headline"])}</h1>
        <p class="hero-copy">{escape(site["hero_text"])}</p>
        <a class="button" href="#content">Explore Recipes &rarr;</a>
      </section>
      <div class="chips"><a class="active" href="#content">All</a>{chips}</div>
      <section id="content" class="recipe-section">
        <div class="section-head">
          <h2>Featured Recipes</h2>
          <a href="#more">View All &rarr;</a>
        </div>
        <div class="recipe-grid" data-section="featured"></div>
      </section>
      <section class="chef-card">
        <div class="chef-photo" aria-hidden="true"></div>
        <div>
          <p class="eyebrow">Meet the Author</p>
          <h2>Hi, I&rsquo;m {chef}</h2>
          {_paragraphs(site["about_text"])}
          <a class="outline-button" href="about.html">Read My Story &rarr;</a>
        </div>
      </section>
      <section class="newsletter">
        <h2>Get Fresh Recipes Weekly</h2>
        <p>Join thousands of home cooks who get new recipes, tips, and seasonal ideas delivered every week.</p>
        <form class="newsletter-form" action="contact.html">
          <label class="sr-only" for="newsletter-email">Email address</label>
          <input id="newsletter-email" type="email" placeholder="your@email.com">
          <button type="submit">Subscribe Free &rarr;</button>
        </form>
      </section>
      {category_sections}
    """
    return _page_shell(site, site["headline"], body, "home")


def _category_page(site: dict, category: str) -> str:
    slug = slugify(category)
    site_categories = site.get("categories") or list(CATEGORY_RECIPES.keys())
    chips = "".join(
        f'<a class="{"active" if name == category else ""}" href="../{slugify(name)}/">{escape(name)}</a>'
        for name in site_categories
    )
    body = f"""
      <section class="page-intro category-intro">
        <div class="breadcrumbs"><a href="../../index.html">Home</a><span>&rsaquo;</span><span>{escape(category)}</span></div>
        <h1>{escape(category)} Recipes</h1>
        <p><span class="recipe-count">Loading recipes...</span></p>
      </section>
      <div class="chips category-chips"><a href="../../index.html#recipes">All</a>{chips}</div>
      <div class="category-layout">
        <section>
          <div class="section-head"><h2>{escape(category)}</h2></div>
          <div class="recipe-grid category-grid" data-category="{escape(category)}"></div>
        </section>
        <aside class="category-sidebar">
          <div class="sidebar-card about-mini">
            <h3>About the Author</h3>
            <div class="sidebar-rule"></div>
            <div class="chef-photo small" aria-hidden="true"></div>
            <h4>{escape(site["chef_name"])}</h4>
            <p>Simple, tested recipes for real home kitchens &mdash; clear steps, everyday ingredients.</p>
            <a class="outline-button small-button" href="../../about.html">Full Story &rarr;</a>
          </div>
          <div class="sidebar-card subscribe-mini">
            <h3>Free Weekly Recipes</h3>
            <div class="sidebar-rule"></div>
            <p>New recipes every week &mdash; straight to your inbox.</p>
            <form class="sidebar-form" action="../../contact.html">
              <label class="sr-only" for="sidebar-email">Email address</label>
              <input id="sidebar-email" type="email" placeholder="your@email.com">
              <button type="submit">Subscribe Free</button>
            </form>
          </div>
          <div class="sidebar-card">
            <h3>Browse Categories</h3>
            <div class="sidebar-rule"></div>
            <div class="sidebar-links">{"".join(f'<a href="../{slugify(name)}/">{escape(name)}<span>&rsaquo;</span></a>' for name in site_categories)}</div>
          </div>
        </aside>
      </div>
    """
    return _page_shell(site, category, body, slug, prefix="../../")


def _recipe_sidebar(site: dict, prefix: str) -> str:
    all_recipes = [(title, mins, cat) for cat, items in CATEGORY_RECIPES.items() for title, mins, _ in items]
    latest_three = all_recipes[:3]
    latest_items = "".join(
        f"""<a class="sidebar-latest-item" href="{prefix}recipe/{slugify(title)}/">
          <div class="sidebar-latest-thumb photo-{slugify(title) if title in RECIPE_IMAGES else 'fallback'}" aria-hidden="true"></div>
          <div class="sidebar-latest-info">
            <span class="sidebar-latest-title">{escape(title)}</span>
            <span class="sidebar-latest-meta">&#9719;&nbsp;{escape(mins)}</span>
          </div>
        </a>"""
        for title, mins, cat in latest_three
    )
    return f"""
      <aside class="category-sidebar recipe-sidebar">
        <div class="sidebar-card about-mini">
          <h3>About Me</h3>
          <div class="sidebar-rule"></div>
          <div class="chef-photo small" aria-hidden="true"></div>
          <h4>{escape(site["chef_name"])}</h4>
          <p>Hi there! I&rsquo;m {escape(site["chef_name"])}, and food has been at the heart of my life for as long as I can remember. Growing up, the kitchen was always the warmest</p>
          <a class="outline-button small-button" href="{prefix}about.html">Full Story &rarr;</a>
        </div>
        <div class="sidebar-card subscribe-mini">
          <h3>Free Weekly Recipes</h3>
          <div class="sidebar-rule"></div>
          <p>New recipes every week &mdash; straight to your inbox.</p>
          <form class="sidebar-form" action="{prefix}contact.html">
            <label class="sr-only" for="recipe-sidebar-email">Email address</label>
            <input id="recipe-sidebar-email" type="email" placeholder="your@email.com">
            <button type="submit">Subscribe Free</button>
          </form>
        </div>
        <div class="sidebar-card">
          <h3>Browse Categories</h3>
          <div class="sidebar-rule"></div>
          <div class="sidebar-links">{"".join(f'<a href="{prefix}category/{slugify(name)}/">{escape(name)}<span>&rsaquo;</span></a>' for name in (site.get("categories") or list(CATEGORY_RECIPES.keys())))}</div>
        </div>
        <div class="sidebar-card sidebar-latest">
          <h3>Latest Recipes</h3>
          <div class="sidebar-rule"></div>
          <div class="sidebar-latest-list">{latest_items}</div>
        </div>
      </aside>
    """


def _recipe_page(site: dict, category: str, title: str, minutes: str, description: str) -> str:
    slug = slugify(title)
    image_class = f"photo-{slug}" if title in RECIPE_IMAGES else "photo-fallback"
    ar_rating, ar_count = _article_rating(title)
    prep_mins, cook_mins, total_mins = _derive_times(minutes)
    prep_str = _format_minutes(prep_mins)
    cook_str = _format_minutes(cook_mins)
    total_str = minutes if _parse_minutes(minutes) > 0 else _format_minutes(total_mins)
    is_bean_sprout = title == "Bean Sprout Salad"
    ingredients = [
        "300g fresh bean sprouts, rinsed and drained",
        "1 small carrot, julienned",
        "1 small cucumber, sliced thin",
        "2 green onions, chopped",
        "1 red bell pepper, sliced thin",
        "2 tablespoons soy sauce",
        "1 tablespoon rice vinegar",
        "1 tablespoon sesame oil",
        "1 tablespoon sesame seeds",
        "Salt and pepper to taste",
    ] if is_bean_sprout else [
        "2 cups fresh vegetables",
        "1 tablespoon olive oil",
        "1 tablespoon soy sauce",
        "1 teaspoon rice vinegar",
        "Fresh herbs to taste",
        "Salt and pepper to taste",
    ]
    instructions = [
        "In a large bowl, combine the bean sprouts, carrot, cucumber, green onions, and red bell pepper.",
        "In a small bowl, whisk together the soy sauce, rice vinegar, and sesame oil until well combined.",
        "Pour the dressing over the vegetable mixture and toss gently to coat.",
        "Sprinkle with sesame seeds and season with salt and pepper to taste.",
        "Serve immediately or refrigerate for up to 2 hours for flavors to develop.",
    ] if is_bean_sprout else [
        "Prepare all ingredients and place them near your work surface.",
        "Whisk together the dressing ingredients until smooth.",
        "Toss everything together gently until evenly coated.",
        "Taste, adjust seasoning, and serve fresh.",
    ]
    ingredient_html = "".join(
        f'<li class="ingredient-item" role="checkbox" aria-checked="false" tabindex="0">'
        f'<span class="ingredient-check" aria-hidden="true">&#10003;</span>'
        f'<span class="ingredient-text">{escape(item)}</span>'
        f'</li>'
        for item in ingredients
    )
    instruction_html = "".join(
        f"<li><span>{index}</span><p>{escape(step)}</p></li>"
        for index, step in enumerate(instructions, start=1)
    )
    body = f"""
      <div class="recipe-layout">
        <article class="recipe-article" data-site-name="{escape(site['website_name'])}">
          <header class="recipe-header">
            <div class="breadcrumbs"><a href="../../index.html">Home</a><span>/</span><a href="../../category/{slugify(category)}/">{escape(category)}</a><span>/</span><span>{escape(title)}</span></div>
            <p class="eyebrow">{escape(category)}</p>
            <h1>{escape(title)}</h1>
            <div class="article-rating"><span class="stars" aria-label="{ar_rating} out of 5 stars"></span><span>{ar_rating}</span><span style="color:var(--line)">&middot;</span><span>{ar_count} ratings</span></div>
            <div class="article-meta"><span>By <strong>{escape(site["chef_name"])}</strong></span><span style="color:var(--line)">&middot;</span><span>May 11, 2026</span></div>
            <div class="article-actions">
              <a class="button" href="#recipe-card">Jump To Recipe &darr;</a>
              <button type="button" onclick="window.print()" aria-label="Print this recipe">&#128424; Print Recipe</button>
            </div>
          </header>
          <div class="recipe-hero-image {image_class}" aria-label="{escape(title)}"></div>
          <p class="recipe-summary">{escape(description)}</p>
          <div class="recipe-stats" id="recipe-card">
            <div><span>Prep Time</span><strong>{escape(prep_str)}</strong></div>
            <div><span>Cook Time</span><strong>{escape(cook_str)}</strong></div>
            <div><span>Total Time</span><strong>{escape(total_str)}</strong></div>
            <div><span>Servings</span><strong>4</strong></div>
          </div>
          <section class="article-section">
            <h2>Ingredients</h2>
            <ul class="ingredient-grid">{ingredient_html}</ul>
          </section>
          <section class="article-section">
            <h2>Instructions</h2>
            <ol class="instruction-list">{instruction_html}</ol>
          </section>
          <div class="tag-list"><span>salad</span><span>vegetarian</span><span>easy</span><span>healthy</span><span>{escape(category.lower())}</span></div>
          <section class="article-section">
            <h2>Nutrition Facts</h2>
            <div class="nutrition-grid">
              <div><span>Calories</span><strong>120 kcal</strong></div>
              <div><span>Protein</span><strong>4 g</strong></div>
              <div><span>Carbs</span><strong>15 g</strong></div>
              <div><span>Fat</span><strong>6 g</strong></div>
            </div>
            <p class="nutrition-note">* Nutritional values are estimates per serving and may vary based on ingredients used.</p>
          </section>
          <section class="article-section">
            <h2>Notes</h2>
            <div class="notes-box">
              <p>Try adding a splash of lime juice for extra freshness.</p>
              <p>Use pre-packaged matchstick carrots for convenience.</p>
              <p>This salad is best enjoyed fresh but can be stored in the fridge for a day.</p>
            </div>
          </section>
          <section class="article-section faq-section">
            <h2>Frequently Asked Questions</h2>
            <div class="faq-item"><h3><span>Q:</span> Can I use canned bean sprouts?</h3><p><strong>A:</strong> Fresh bean sprouts are recommended for the best texture, but canned can be used in a pinch. Rinse them well before use.</p></div>
            <div class="faq-item"><h3><span>Q:</span> Is this salad vegan?</h3><p><strong>A:</strong> Yes, this bean sprout salad is vegan-friendly.</p></div>
            <div class="faq-item"><h3><span>Q:</span> How do I store leftovers?</h3><p><strong>A:</strong> Store leftovers in an airtight container in the fridge for up to 24 hours.</p></div>
          </section>
          <section class="article-section comments-section">
            <h2>Comments</h2>
            <form class="comment-form">
              <input type="text" placeholder="Your name">
              <input type="email" placeholder="your@email.com">
              <textarea placeholder="Share a tip, a substitution, or how it turned out for you..."></textarea>
              <button type="submit">Post Comment</button>
            </form>
            <p class="no-comments">No comments yet &mdash; be the first to leave one!</p>
          </section>
        </article>
        {_recipe_sidebar(site, "../../")}
      </div>
    """
    image_filename = RECIPE_IMAGES.get(title, "")
    image_url = f"../../assets/{image_filename}" if image_filename else ""
    schema = f"""  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": {_json_str(title)},
    "description": {_json_str(description)},
    "author": {{"@type": "Person", "name": {_json_str(site["chef_name"])}}},
    "datePublished": "2026-05-11",
    "prepTime": "{_iso_duration(prep_mins)}",
    "cookTime": "{_iso_duration(cook_mins)}",
    "totalTime": "{_iso_duration(total_mins)}",
    "recipeYield": "4 servings",
    "recipeCategory": {_json_str(category)},
    "image": {_json_str(image_url)},
    "nutrition": {{
      "@type": "NutritionInformation",
      "calories": "120 calories",
      "proteinContent": "4 g",
      "carbohydrateContent": "15 g",
      "fatContent": "6 g"
    }},
    "aggregateRating": {{
      "@type": "AggregateRating",
      "ratingValue": "4.6",
      "reviewCount": "183"
    }}
  }}
  </script>
  <script>
  (function(){{
    var SLUG = {_json_str(slug)};
    var KEY  = 'recipe_ingredient_state_' + SLUG;

    function save(states) {{
      try {{ localStorage.setItem(KEY, JSON.stringify(states)); }} catch(e) {{}}
    }}
    function load() {{
      try {{ return JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch(e) {{ return {{}}; }}
    }}

    function toggle(item, index, states) {{
      var checked = item.getAttribute('aria-checked') === 'true';
      checked = !checked;
      item.setAttribute('aria-checked', String(checked));
      item.classList.toggle('checked', checked);
      states[index] = checked;
      save(states);
    }}

    document.addEventListener('DOMContentLoaded', function() {{
      var items  = document.querySelectorAll('.ingredient-item');
      var states = load();

      items.forEach(function(item, i) {{
        // Restore saved state
        if (states[i]) {{
          item.setAttribute('aria-checked', 'true');
          item.classList.add('checked');
        }}

        item.addEventListener('click', function() {{ toggle(item, i, states); }});

        item.addEventListener('keydown', function(e) {{
          if (e.key === ' ' || e.key === 'Enter') {{
            e.preventDefault();
            toggle(item, i, states);
          }}
        }});
      }});
    }});
  }})();
  </script>\n"""
    return _page_shell(site, title, body, category.lower(), prefix="../../", extra_head=schema)


def _about_page(site: dict) -> str:
    website_name = escape(site["website_name"])
    chef = escape(site["chef_name"])
    body = f"""
      <section class="page-intro">
        <div class="breadcrumbs"><a href="index.html">Home</a><span>&rsaquo;</span><span>About Us</span></div>
        <h1>About Us</h1>
        <p>The story behind {website_name}</p>
      </section>
      <section class="about-story">
        <div class="chef-photo about-photo" aria-hidden="true"></div>
        <article>
          <h2>Hi, I'm {chef}</h2>
          <p>Hi there! I'm {chef}, and food has been at the heart of my life for as long as I can remember.</p>
          <p>Growing up, the kitchen was always the warmest place in our home. I still remember the smell of freshly baked bread, simple family dinners, and those little moments that somehow made everything feel complete.</p>
          <p>Over the years, I found myself coming back to the kitchen again and again not just to cook, but to feel grounded, creative, and connected. What started as small experiments and handwritten recipes slowly turned into something much bigger.</p>
          <p>Every recipe you find here is made in a real kitchen, tested with care, and designed for everyday life. No fancy techniques, no hard-to-find ingredients, just honest cooking that works.</p>
          <p>Whether you're looking for quick meals, cozy dishes, or something special to share, you're in the right place. And if you enjoy discovering new recipes, don't forget to come back often.</p>
        </article>
      </section>
      <section class="mission-card">
        <h2>Our Mission</h2>
        <p>At {website_name}, we believe great food doesn't have to be complicated.</p>
        <p>Our mission is simple: to share easy, reliable, and delicious recipes that anyone can make at home &mdash; no stress, no guesswork.</p>
        <p>Every recipe on this site is carefully tested, adjusted, and written with real people in mind. We focus on simple ingredients, clear instructions, and results you can trust every time.</p>
        <p>We want cooking to feel enjoyable, not overwhelming. A place where you can find inspiration, try something new, and create meals that bring comfort and happiness to your everyday life.</p>
      </section>
      <div class="page-actions">
        <a class="button" href="index.html#recipes">Browse All Recipes &rarr;</a>
        <a class="outline-button" href="contact.html">Get in Touch</a>
      </div>
    """
    return _page_shell(site, f"About {site['website_name']}", body, "about")


def _contact_page(site: dict) -> str:
    body = f"""
      <section class="page-intro">
        <div class="breadcrumbs"><a href="index.html">Home</a><span>&rsaquo;</span><span>Contact</span></div>
        <h1>Contact Us</h1>
        <p>We'd love to hear from you &mdash; recipe questions, feedback, or just to say hello.</p>
      </section>
      <section class="contact-page">
        <p>Have a question about a recipe? Want to share a photo of something you made? Just fill in the form below and we'll get back to you as soon as we can.</p>
        <form class="contact-form" action="contact.html">
          <label for="contact-name">Your Name *</label>
          <input id="contact-name" type="text" placeholder="Jane Smith">
          <label for="contact-email">Email Address *</label>
          <input id="contact-email" type="email" placeholder="jane@example.com">
          <label for="contact-subject">Subject</label>
          <input id="contact-subject" type="text" placeholder="Recipe question, feedback, etc.">
          <label for="contact-message">Message *</label>
          <textarea id="contact-message" placeholder="Tell us what's on your mind..."></textarea>
          <button type="submit">Send Message &rarr;</button>
        </form>
      </section>
    """
    return _page_shell(site, "Contact", body, "contact")


def _privacy_policy_html(site: dict) -> str:
    return _privacy_policy_sections(site)[1]


def _terms_of_service_html(site: dict) -> str:
    return _terms_of_service_sections(site)[1]


def _disclaimer_html(site: dict) -> str:
    return _disclaimer_sections(site)[1]


def _legal_page(site: dict, key: str, title: str, fallback: str) -> str:
    policy = site.get(key) or fallback
    if title == "Privacy Policy" and not site.get(key):
        content = _privacy_policy_html(site)
    elif title == "Terms of Use" and not site.get(key):
        content = _terms_of_service_html(site)
    elif title == "Disclaimer" and not site.get(key):
        content = _disclaimer_html(site)
    else:
        content = _paragraphs(policy)
    updated = escape(site.get("effective_date") or "May 11, 2026")
    body = f"""
      <section class="page-intro legal-intro">
        <div class="breadcrumbs"><a href="index.html">Home</a><span>&rsaquo;</span><span>{escape(title)}</span></div>
        <h1>{escape(title)}</h1>
      </section>
      <section class="policy-page">
        <p>Last updated: {updated}</p>
        <hr>
        {content}
      </section>
    """
    return _page_shell(site, title, body, key)


def _style(site: dict) -> str:
    photo_rules = "\n".join(
        f".photo-{slugify(title)} {{ background-image: linear-gradient(180deg, rgba(0,0,0,.03), rgba(0,0,0,.05)), url('assets/{filename}'); }}"
        for title, filename in sorted(RECIPE_IMAGES.items())
    )
    chef_photo_rule = (
        f""".chef-photo {{
  background-image: linear-gradient(180deg, rgba(0,0,0,.02), rgba(0,0,0,.04)), url('assets/{site["chef_image_filename"]}');
  background-size: cover;
  background-position: center;
}}
.chef-photo.small {{
  background-image: linear-gradient(180deg, rgba(0,0,0,.02), rgba(0,0,0,.04)), url('assets/{site["chef_image_filename"]}');
  background-size: cover;
  background-position: center;
}}
"""
        if site.get("chef_image_filename")
        else ""
    )
    theme = _resolve_theme(site)
    theme_vars = _theme_css(theme)
    root_block = (
        "\n/* ═══════════════════════════════════════════════════\n"
        "   DESIGN SYSTEM — Premium Editorial Blog\n"
        "   ═══════════════════════════════════════════════════ */\n"
        ":root {" + theme_vars + "\n"
        "\n  /* Structural defaults (non-theme) */\n"
        "\n  /* Shadows — layered for depth */\n"
        "  --shadow-sm:0 1px 3px rgba(20,20,16,.07), 0 4px 12px rgba(20,20,16,.05);\n"
        "  --shadow-md:0 4px 16px rgba(20,20,16,.08), 0 12px 32px rgba(20,20,16,.06);\n"
        "  --shadow-lg:0 8px 24px rgba(20,20,16,.08), 0 24px 56px rgba(20,20,16,.10);\n"
        "  --shadow-hover:0 16px 48px rgba(20,20,16,.14), 0 4px 12px rgba(20,20,16,.06);\n"
        "\n  /* Radii */\n"
        "  --r-sm:6px;\n  --r-md:10px;\n  --r-lg:16px;\n  --r-pill:999px;\n"
        "\n  /* Spacing */\n"
        "  --section-pad:80px 28px;\n  --content-max:1280px;\n}\n"
    )
    font_import = "@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Bree+Serif&display=swap');\n"
    return font_import + root_block + """

/* ── Reset & base ─────────────────────────────────── */
*, *::before, *::after { box-sizing:border-box; }
html {
  scroll-behavior:smooth;
  -webkit-text-size-adjust:100%;
  font-size:clamp(14px, 1.2vw, 17px);
}
body {
  margin:0;
  font-family: Lora, "Source Serif 4", Georgia, serif;
  font-size:1em;
  line-height:1.65;
  color:var(--ink);
  background:var(--paper);
  text-rendering:optimizeLegibility;
  -webkit-font-smoothing:antialiased;
  overflow-x:hidden;
}
h1, h2, h3, h4, h5, h6 {
  font-family:"Bree Serif", Georgia, serif;
  font-weight:400;
  font-synthesis:none;
  letter-spacing:-.02em;
  color:#111111;
  text-rendering:optimizeLegibility;
  -webkit-font-smoothing:antialiased;
}
a {
  color:inherit;
  text-decoration:none;
  -webkit-tap-highlight-color:transparent;
}
img {
  max-width:100%;
  display:block;
  height:auto;
}
button {
  font-family:inherit;
  -webkit-tap-highlight-color:transparent;
}
.sr-only {
  position:absolute;
  width:1px;
  height:1px;
  padding:0;
  margin:-1px;
  overflow:hidden;
  clip:rect(0,0,0,0);
  white-space:nowrap;
  border:0;
}

/* ── Header ───────────────────────────────────────── */
.site-header {
  position:sticky;
  top:0;
  z-index:100;
  width:100%;
  border-bottom:1px solid var(--line);
  background:rgba(255,255,255,.97);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  box-shadow:0 1px 0 var(--line), 0 4px 20px rgba(20,20,16,.04);
  backdrop-filter:blur(12px);
}
.header-inner {
  max-width:var(--content-max);
  min-height:72px;
  margin:0 auto;
  padding:0 28px;
  display:grid;
  grid-template-columns:240px 1fr auto;
  align-items:center;
  gap:24px;
}
.nav-toggle {
  display:none;
}
@media (max-width: 767px) {
  .nav-toggle { display:flex; }
}
@media (min-width: 768px) {
  .nav-toggle { display:none !important; }
}

/* ── Brand ────────────────────────────────────────── */
.brand {
  display:flex;
  align-items:center;
  gap:10px;
  justify-self:start;
  min-width:0;
}
.brand-logo {
  width:46px;
  height:46px;
  object-fit:contain;
  flex:0 0 auto;
}
.brand.logo-only .brand-logo {
  width:min(140px, 100%);
  height:52px;
  object-fit:contain;
  object-position:left center;
}
.brand-text { display:grid; gap:1px; min-width:0; }
.brand strong, .footer-brand {
  display:block;
  font-family:"Bree Serif", Georgia, serif;
  font-size:1.48rem;
  line-height:1;
  font-weight:400;
  letter-spacing:-.01em;
}
.brand-text > span {
  color:var(--muted-light);
  font-size:.72rem;
  font-weight:700;
  letter-spacing:.14em;
  text-transform:uppercase;
}

/* ── Navigation ───────────────────────────────────── */
nav {
  display:flex;
  justify-content:center;
  align-items:center;
  gap:2px;
  font-size:.92rem;
  font-weight:700;
}
nav a {
  min-height:40px;
  display:inline-flex;
  align-items:center;
  padding:0 14px;
  border-radius:var(--r-sm);
  color:var(--ink-soft);
  letter-spacing:.01em;
  transition:background .18s, color .18s;
}
nav a.active { color:var(--gold); background:var(--gold-pale); }
nav a:hover:not(.active) { color:var(--ink); background:var(--cream); }

/* ── Search bar ───────────────────────────────────── */
.site-search {
  height:40px;
  display:flex;
  justify-self:end;
  border:1.5px solid var(--line);
  border-radius:var(--r-pill);
  overflow:hidden;
  background:var(--cream);
  transition:border-color .18s, box-shadow .18s;
}
.site-search:focus-within {
  border-color:var(--gold);
  box-shadow:0 0 0 3px rgba(232,160,0,.12);
}
.site-search input {
  width:180px;
  border:0;
  padding:0 16px;
  outline:0;
  font:inherit;
  font-size:.9rem;
  color:var(--ink);
  background:transparent;
}
.site-search input::placeholder { color:var(--muted-light); }
.site-search button {
  width:42px;
  border:0;
  border-left:1.5px solid var(--line);
  background:transparent;
  color:var(--gold);
  font-size:1.1rem;
  cursor:pointer;
  transition:background .18s;
}
.site-search button:hover { background:var(--gold-pale); }

/* ── Main ─────────────────────────────────────────── */
main {
  max-width:none;
  margin:0;
  padding:0;
  overflow-x:hidden;
}

/* ── Hero ─────────────────────────────────────────── */
.hero {
  min-height:460px;
  display:grid;
  align-content:center;
  justify-items:center;
  text-align:center;
  padding:88px 24px 80px;
  border-bottom:1px solid var(--line-soft);
  background:linear-gradient(180deg, #fdfaf4 0%, #fff 100%);
}
.eyebrow {
  margin:0;
  color:var(--gold);
  font-size:.76rem;
  font-weight:800;
  letter-spacing:.22em;
  line-height:1.5;
  text-transform:uppercase;
}
.hero h1 {
  margin:16px 0 18px;
  max-width:760px;
  font-size:clamp(2.2rem, 4vw, 3rem);
  font-weight:700;
  line-height:1.08;
  letter-spacing:-.02em;
  color:#111111;
}
.hero-copy {
  max-width:600px;
  margin:0;
  color:var(--muted);
  font-size:1.15rem;
  line-height:1.65;
}

/* ── Buttons ──────────────────────────────────────── */
.button,
.newsletter-form button,
.outline-button {
  min-height:48px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius:var(--r-pill);
  font-weight:700;
  font-size:.95rem;
  letter-spacing:.01em;
  transition:transform .2s cubic-bezier(.34,1.56,.64,1), box-shadow .2s ease, background .18s;
  touch-action:manipulation;
}
.button {
  margin-top:28px;
  padding:0 32px;
  background:var(--gold);
  color:white;
  box-shadow:0 4px 16px rgba(232,160,0,.28), 0 1px 3px rgba(232,160,0,.18);
}
.button:hover,
.button:active {
  transform:translateY(-2px);
  box-shadow:0 8px 24px rgba(232,160,0,.35), 0 2px 6px rgba(232,160,0,.20);
}
.button:active { transform:translateY(0); }
.outline-button {
  margin-top:18px;
  padding:0 30px;
  border:1.5px solid var(--green);
  color:var(--green);
  background:white;
}
.outline-button:hover,
.outline-button:active {
  transform:translateY(-2px);
  background:var(--green);
  color:white;
}
.outline-button:active { transform:translateY(0); }
.newsletter-form button:hover,
.newsletter-form button:active {
  transform:translateY(-2px);
  background:#b85f2f;
}
.newsletter-form button:active { transform:translateY(0); }

/* ── Touch-Friendly Forms ──────────────────────────── */
input[type="text"],
input[type="email"],
input[type="search"],
input[type="number"],
textarea,
select {
  font-size:16px;
  touch-action:manipulation;
}
@media (max-width: 767px) {
  input,
  textarea,
  select,
  button {
    font-size:16px !important;
  }
}

/* ── Category chips ───────────────────────────────── */
.chips {
  display:flex;
  justify-content:center;
  flex-wrap:wrap;
  gap:10px;
  padding:26px 20px;
  border-bottom:1px solid var(--line-soft);
  background:#faf8f2;
}
.chips a {
  min-height:40px;
  display:inline-flex;
  align-items:center;
  padding:0 18px;
  border:1.5px solid var(--line);
  border-radius:var(--r-pill);
  background:white;
  color:var(--ink-soft);
  font-size:.88rem;
  font-weight:700;
  box-shadow:var(--shadow-sm);
  transition:border-color .18s, background .18s, color .18s, transform .18s;
}
.chips a.active,
.chips a:hover {
  border-color:var(--gold);
  background:var(--gold);
  color:white;
  transform:translateY(-1px);
}

/* ── Recipe sections ──────────────────────────────── */
.recipe-section {
  max-width:var(--content-max);
  margin:0 auto;
  padding:64px 28px;
}
.section-head {
  display:flex;
  justify-content:space-between;
  align-items:baseline;
  gap:16px;
  margin-bottom:36px;
}
.section-head h2 {
  position:relative;
  margin:0;
  padding-bottom:14px;
  font-size:clamp(1.75rem, 3vw, 3rem);
  font-weight:700;
  line-height:1.1;
  letter-spacing:-.02em;
  color:#111111;
}
.section-head h2::after {
  position:absolute;
  left:0;
  bottom:0;
  width:40px;
  height:3px;
  border-radius:var(--r-pill);
  content:"";
  background:var(--gold);
}
.section-head a { color:var(--green); font-weight:700; font-size:.9rem; letter-spacing:.02em; transition:color .18s; }
.section-head a:hover { color:var(--green-dark); }

/* ── Recipe cards ─────────────────────────────────── */
.recipe-grid {
  display:grid;
  grid-template-columns:repeat(3, minmax(0, 1fr));
  gap:28px;
}
.recipe-card {
  overflow:hidden;
  border:1px solid var(--line-soft);
  border-radius:var(--r-lg);
  background:white;
  box-shadow:var(--shadow-sm);
  transition:transform .28s cubic-bezier(.34,1.2,.64,1), box-shadow .28s ease;
}
.recipe-card > a { display:block; height:100%; }
.recipe-card:hover { transform:translateY(-5px); box-shadow:var(--shadow-hover); }
.recipe-photo {
  position:relative;
  height:232px;
  background-color:#e8dece;
  background-size:cover;
  background-position:center;
  overflow:hidden;
}
.recipe-photo::after {
  content:"";
  position:absolute;
  inset:0;
  background:linear-gradient(180deg, transparent 50%, rgba(0,0,0,.22) 100%);
}
.photo-fallback { background-image:linear-gradient(145deg,#c07840 0%,#e8c97a 48%,#5a7a38 100%); }
""" + photo_rules + """
.recipe-photo span {
  position:absolute;
  top:14px;
  left:14px;
  z-index:2;
  display:inline-flex;
  min-height:26px;
  align-items:center;
  padding:0 12px;
  border-radius:var(--r-pill);
  background:rgba(255,255,255,.92);
  color:var(--ink);
  font-size:.7rem;
  font-weight:800;
  letter-spacing:.08em;
  text-transform:uppercase;
  box-shadow:0 2px 8px rgba(0,0,0,.12);
  backdrop-filter:blur(4px);
}
.recipe-body { padding:20px 22px 20px; }
.recipe-card h3 {
  margin:0 0 10px;
  font-size:1.25rem;
  font-weight:700;
  line-height:1.2;
  letter-spacing:-.02em;
  color:#111111;
}
.recipe-card p {
  margin:0 0 16px;
  color:var(--muted);
  font-size:.93rem;
  line-height:1.55;
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  overflow:hidden;
}
.recipe-meta {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
  padding-top:14px;
  border-top:1px solid var(--line-soft);
  color:var(--muted);
  font-size:.83rem;
}
.stars { color:var(--muted-light); letter-spacing:.03em; white-space:nowrap; }
.stars::before { content:"\\2605\\2605\\2605\\2605\\2605 "; color:var(--gold-light); }

/* ── Newsletter ───────────────────────────────────── */
.newsletter {
  width:100%;
  margin:0;
  padding:80px 24px;
  color:white;
  text-align:center;
  background:#2C1910;
}
.newsletter h2 {
  margin:0;
  font-size:clamp(1.7rem, 3vw, 2.4rem);
  font-weight:700;
  line-height:1.1;
  letter-spacing:-.02em;
  color:#ffffff;
}
.newsletter p { margin:18px auto 0; max-width:560px; color:rgba(255,255,255,.82); font-size:1.05rem; line-height:1.65; }
.newsletter-form { display:flex; justify-content:center; gap:12px; margin:30px auto 0; max-width:520px; }
.newsletter-form input {
  min-height:50px;
  flex:1;
  border:0;
  border-radius:var(--r-md);
  padding:0 20px;
  color:var(--ink);
  font:inherit;
  font-size:.95rem;
  background:#ffffff;
  outline:0;
}
.newsletter-form button {
  padding:0 28px;
  border:0;
  border-radius:var(--r-pill);
  background:#c96f3d;
  color:#ffffff;
  font-size:.95rem;
  font-weight:700;
  cursor:pointer;
  box-shadow:0 4px 16px rgba(201,111,61,.35);
}

/* ── Chef / author card ───────────────────────────── */
.chef-card {
  max-width:var(--content-max);
  margin:0 auto;
  padding:72px 28px;
  display:grid;
  grid-template-columns:280px minmax(0, 1fr);
  gap:64px;
  align-items:center;
  border-top:1px solid var(--line-soft);
}
.chef-photo {
  width:100%;
  aspect-ratio:4/5;
  border-radius:var(--r-lg);
  background:
    radial-gradient(circle at 48% 28%, #f2d2bf 0 12%, transparent 13%),
    radial-gradient(circle at 44% 22%, #c89a77 0 18%, transparent 19%),
    linear-gradient(160deg, #9a6a45 0%, #f5d0a8 46%, #4e3427 100%);
  box-shadow:var(--shadow-lg);
}
.chef-card h2 { margin:0 0 18px; font-size:clamp(1.8rem, 2.5vw, 2.4rem); line-height:1.1; letter-spacing:-.02em; }
.chef-card p, .content-page p { color:var(--muted); font-size:1.06rem; line-height:1.72; }

/* ── Page intros ──────────────────────────────────── */
.all-recipes { padding-top:24px; }
.center-action { display:flex; justify-content:center; margin-top:36px; }
.page-hero, .category-hero, .page-intro {
  max-width:var(--content-max);
  margin:0 auto;
  padding:52px 28px 44px;
}
.page-hero.compact { padding-bottom:24px; }
.page-hero h1, .category-hero h1, .page-intro h1 {
  margin:16px 0 12px;
  font-size:clamp(2.1rem, 4vw, 3rem);
  line-height:1.06;
  letter-spacing:-.02em;
}
.page-intro p, .category-hero p { margin:0; color:var(--muted); font-size:1.05rem; line-height:1.6; }
.breadcrumbs { display:flex; gap:8px; color:var(--muted-light); font-size:.82rem; }
.breadcrumbs a { color:var(--muted-light); transition:color .15s; }
.breadcrumbs a:hover { color:var(--ink); }
.category-intro, .legal-intro { border-bottom:1px solid var(--line); }
.category-chips a.active { background:var(--gold); color:white; border-color:var(--gold); }

/* ── Category layout ──────────────────────────────── */
.category-layout {
  max-width:var(--content-max);
  margin:0 auto;
  padding:56px 28px 64px;
  display:grid;
  grid-template-columns:minmax(0, 1fr) 310px;
  gap:48px;
  align-items:start;
}
.category-grid { grid-template-columns:repeat(3, minmax(0, 1fr)); gap:24px; }
.category-grid .recipe-photo { height:190px; }
.category-grid .recipe-card h3 { font-size:1.1rem; }

/* ── Sidebar ──────────────────────────────────────── */
.category-sidebar {
  display:flex;
  flex-direction:column;
  gap:20px;
}
.sidebar-card {
  border:1px solid var(--line-soft);
  border-radius:var(--r-md);
  padding:22px 20px;
  background:var(--cream);
  box-shadow:var(--shadow-sm);
}
.sidebar-card h3 {
  margin:0 0 24px;
  font-family:"Bree Serif", Georgia, serif;
  font-size:1.125rem;
  font-weight:400;
  line-height:1.2;
  letter-spacing:-.3px;
  text-transform:none;
  color:#1d1a17;
  padding-bottom:18px;
  border-bottom:1px solid #e2d7cd;
}
.sidebar-card h4 { margin:14px 0 6px; font-size:.96rem; text-align:center; color:var(--ink); }
.sidebar-card p { color:#6f6962; font-size:1rem; line-height:1.7; margin:8px 0 0; }
.sidebar-rule { display:none; }
.about-mini { text-align:center; }
.chef-photo.small {
  width:76px;
  aspect-ratio:1;
  border:3px solid var(--gold);
  border-radius:50%;
  margin:0 auto;
  background:
    radial-gradient(circle at 50% 34%, #f2d2bf 0 16%, transparent 17%),
    radial-gradient(circle at 46% 27%, #b9825b 0 22%, transparent 23%),
    linear-gradient(160deg, #8b623f 0%, #f1c49e 52%, #594138 100%);
  box-shadow:0 6px 18px rgba(20,20,16,.14);
}
""" + chef_photo_rule + """
.small-button { min-height:40px; margin-top:12px; padding:0 22px; font-size:.88rem; }
.sidebar-form { display:grid; gap:10px; margin-top:14px; }
.sidebar-form input,
.contact-form input,
.contact-form textarea {
  width:100%;
  border:1.5px solid var(--line);
  border-radius:var(--r-sm);
  padding:0 14px;
  color:var(--ink);
  font:inherit;
  font-size:.92rem;
  background:white;
  outline:0;
  transition:border-color .18s, box-shadow .18s;
}
.sidebar-form input:focus,
.contact-form input:focus,
.contact-form textarea:focus {
  border-color:var(--gold);
  box-shadow:0 0 0 3px rgba(232,160,0,.1);
}
.sidebar-form input { min-height:44px; }
.sidebar-form button,
.contact-form button {
  min-height:46px;
  border:0;
  border-radius:var(--r-pill);
  background:var(--gold);
  color:white;
  font:inherit;
  font-size:.9rem;
  font-weight:700;
  cursor:pointer;
  box-shadow:0 3px 12px rgba(232,160,0,.25);
  transition:transform .18s, box-shadow .18s;
}
.sidebar-form button:hover,
.contact-form button:hover { transform:translateY(-1px); box-shadow:0 6px 18px rgba(232,160,0,.32); }
.sidebar-links a {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:10px 0;
  border-bottom:1px solid var(--line-soft);
  color:var(--ink-soft);
  font-size:.9rem;
  transition:color .15s, padding-left .15s;
}
.sidebar-links a:last-child { border-bottom:0; }
.sidebar-links a:hover { color:var(--gold); padding-left:4px; }
.sidebar-links span { color:var(--line); }

/* ── Sidebar Latest Recipes widget ───────────────── */
.sidebar-latest-list { display:grid; gap:0; }
.sidebar-latest-item {
  display:grid;
  grid-template-columns:72px minmax(0,1fr);
  gap:14px;
  align-items:center;
  padding-bottom:16px;
  margin-bottom:16px;
  border-bottom:1px solid #ece2d8;
  text-decoration:none;
  transition:opacity .15s;
}
.sidebar-latest-item:last-child { border-bottom:0; margin-bottom:0; padding-bottom:0; }
.sidebar-latest-item:hover { opacity:.78; }
.sidebar-latest-thumb {
  width:72px;
  height:72px;
  border-radius:12px;
  background-size:cover;
  background-position:center;
  background-color:var(--line);
  flex-shrink:0;
}
.sidebar-latest-info { display:flex; flex-direction:column; gap:5px; }
.sidebar-latest-title {
  font-family:"Bree Serif",Georgia,serif;
  font-size:1.125rem;
  font-weight:700;
  line-height:1.35;
  color:#1f1b18;
}
.sidebar-latest-meta {
  font-family:Georgia,serif;
  font-size:.9375rem;
  font-weight:400;
  color:#7b746d;
}
.latest-list { display:grid; gap:0; }
.latest-recipe {
  display:grid;
  grid-template-columns:58px minmax(0, 1fr);
  gap:12px;
  align-items:center;
  padding:10px 0;
  border-bottom:1px solid var(--line-soft);
  transition:opacity .15s;
}
.latest-recipe:last-child { border-bottom:0; }
.latest-recipe:hover { opacity:.8; }
.latest-thumb {
  width:58px;
  height:58px;
  border-radius:var(--r-sm);
  background-size:cover;
  background-position:center;
  background-color:var(--line);
}
.latest-recipe strong { display:block; color:var(--ink); font-size:.87rem; line-height:1.3; }
.latest-recipe small { display:block; margin-top:5px; color:var(--muted-light); font-size:.76rem; }

/* ── About/contact/legal pages ────────────────────── */
.content-page { max-width:820px; margin:0 auto; padding:18px 28px 72px; }
.about-story {
  max-width:960px;
  margin:0 auto;
  padding:64px 28px 36px;
  display:grid;
  grid-template-columns:220px minmax(0, 1fr);
  gap:56px;
  align-items:start;
}
.about-photo {
  aspect-ratio:1;
  border:4px solid var(--gold);
  border-radius:50%;
  box-shadow:var(--shadow-md);
}
.about-story h2 { margin:0 0 18px; font-size:2.1rem; line-height:1.1; letter-spacing:-.02em; }
.about-story p,
.policy-page p,
.policy-page li,
.contact-page p {
  color:#4f5752;
  font-size:1.1rem;
  line-height:1.72;
}
.mission-card {
  max-width:960px;
  margin:32px auto 0;
  padding:34px 38px;
  border:1px solid var(--line-soft);
  border-radius:var(--r-md);
  background:var(--cream);
}
.mission-card h2 { margin:0 0 16px; font-size:1.42rem; letter-spacing:-.01em; }
.mission-card p { margin:0 0 6px; color:var(--muted); font-size:1rem; line-height:1.65; }
.page-actions {
  max-width:960px;
  margin:38px auto 64px;
  padding:0 28px;
  display:flex;
  gap:16px;
}
.contact-page {
  max-width:680px;
  margin:0 auto;
  padding:60px 28px 72px;
}
.contact-form { display:grid; gap:14px; margin-top:30px; }
.contact-form label { margin-top:8px; font-size:.88rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); }
.contact-form input { min-height:50px; }
.contact-form textarea { min-height:170px; padding-top:14px; resize:vertical; }
.contact-form button { width:max-content; min-width:200px; margin-top:6px; padding:0 30px; }
.policy-page {
  max-width:860px;
  margin:0 auto;
  padding:64px 28px 80px;
}
.policy-page hr { border:0; border-top:1px solid var(--line); margin:24px 0 16px; }
.policy-page h2 { margin:38px 0 10px; font-size:1.32rem; letter-spacing:-.01em; }
.policy-page ul { padding-left:24px; }
.contact-box { display:grid; gap:10px; padding:26px; background:white; border:1px solid var(--line); border-radius:var(--r-md); box-shadow:var(--shadow-sm); }

/* ── Recipe page (article) ────────────────────────── */
.recipe-layout {
  max-width:1200px;
  margin:0 auto;
  padding:52px 28px 80px;
  display:grid;
  grid-template-columns:1fr 320px;
  gap:40px;
  align-items:start;
}
.recipe-article { min-width:0; background:var(--paper); }

/* ── Recipe header ────────────────────────────────── */
.recipe-header {
  max-width:680px;
  padding:6px 0 12px;
  border-bottom:1px solid var(--line-soft);
}
.recipe-header .breadcrumbs {
  font-size:.875rem;
  font-weight:500;
  color:#8A8A8A;
  margin-bottom:14px;
}
.recipe-header .eyebrow {
  font-size:.8125rem;
  font-weight:600;
  letter-spacing:2px;
  text-transform:uppercase;
  color:var(--color-primary);
  margin:0 0 10px;
}
.recipe-header h1 {
  margin:0 0 14px;
  font-family:"Bree Serif", Georgia, serif;
  font-size:clamp(1.875rem, 4vw, 2.625rem);
  font-weight:400;
  line-height:1.05;
  letter-spacing:-1px;
  color:#111111;
  max-width:620px;
}
.article-rating {
  display:flex;
  flex-wrap:wrap;
  align-items:center;
  gap:6px;
  margin-top:0;
  margin-bottom:16px;
  font-size:.9375rem;
  line-height:1;
}
.article-rating .stars {
  display:flex;
  align-items:center;
  font-size:.875rem;
  line-height:1;
  letter-spacing:1px;
  color:#e5a100;
  transform:scale(.9);
  transform-origin:left center;
}
.article-rating .stars::before { color:#e5a100; font-size:.875rem; }
.article-rating span:not(.stars) {
  font-family:Georgia, serif;
  font-size:.875rem;
  font-weight:500;
  color:#555555;
  line-height:1;
}
.article-rating span[style] { font-size:.875rem; color:#b5b5b5; line-height:1; }
.article-meta {
  display:flex;
  flex-wrap:wrap;
  align-items:center;
  gap:12px;
  font-size:.9375rem;
  color:#666666;
  margin-bottom:20px;
}
.article-actions {
  display:flex;
  flex-wrap:wrap;
  align-items:center;
  gap:10px;
  margin-bottom:24px;
}
.article-actions .button {
  margin-top:0;
  padding:0 20px;
  min-height:46px;
  border-radius:10px;
  font-size:1rem;
  font-weight:600;
}
.article-actions button {
  min-height:46px;
  padding:0 20px;
  border:1.5px solid var(--line);
  border-radius:10px;
  color:var(--muted);
  background:var(--cream);
  font:inherit;
  font-size:1rem;
  font-weight:600;
  cursor:pointer;
  transition:border-color .18s, background .18s, color .18s;
}
.article-actions button:hover {
  border-color:var(--ink-soft);
  background:var(--paper);
  color:var(--ink);
}

/* ── Article hero image ───────────────────────────── */
.recipe-hero-image {
  aspect-ratio:16/10;
  margin-bottom:28px;
  border-radius:18px;
  background-color:var(--line-soft);
  background-size:cover;
  background-position:center;
  box-shadow:var(--shadow-md);
  overflow:hidden;
}

/* ── Article content ──────────────────────────────── */
.recipe-summary {
  margin:0 0 42px;
  color:#4E4E4E;
  font-size:1.375rem;
  line-height:1.6;
}
.recipe-stats {
  display:grid;
  grid-template-columns:repeat(4, minmax(0, 1fr));
  margin-bottom:48px;
  border:1px solid var(--line-soft);
  border-radius:12px;
  background:var(--cream);
  overflow:hidden;
  box-shadow:var(--shadow-sm);
}
.recipe-stats div { padding:18px 20px; text-align:center; }
.recipe-stats div + div { border-left:1px solid var(--line-soft); }
.recipe-stats span,
.nutrition-grid span {
  display:block;
  color:#8b8176;
  font-size:.688rem;
  font-weight:600;
  letter-spacing:.14em;
  text-transform:uppercase;
}
.recipe-stats strong {
  display:block;
  margin-top:6px;
  font-size:1.125rem;
  font-weight:700;
  color:#2a241f;
  line-height:1.2;
}
.nutrition-grid strong {
  display:block;
  margin-top:6px;
  font-size:1.125rem;
  font-weight:700;
  color:var(--ink);
  line-height:1.2;
}
.article-section { padding:44px 0 0; }
.article-section h2 {
  position:relative;
  margin:0 0 22px;
  padding-bottom:14px;
  border-bottom:1px solid var(--line-soft);
  font-size:1.5rem;
  font-weight:400;
  line-height:1.15;
  letter-spacing:-.01em;
}
.article-section h2::after {
  position:absolute;
  left:0;
  bottom:-1px;
  width:38px;
  height:2px;
  content:"";
  background:var(--gold);
}
.ingredient-grid {
  display:grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:10px;
  list-style:none;
  margin:0;
  padding:0;
}
.ingredient-item {
  display:flex;
  gap:10px;
  align-items:center;
  min-height:50px;
  padding:10px 14px;
  border:1px solid var(--line-soft);
  border-radius:var(--r-sm);
  background:var(--paper);
  color:#4a5350;
  font-size:1rem;
  line-height:1.35;
  cursor:pointer;
  user-select:none;
  transition:background .18s, opacity .2s, border-color .18s;
  outline-offset:2px;
}
.ingredient-item:hover {
  background:var(--cream);
  border-color:var(--line);
}
.ingredient-item:focus-visible {
  outline:2px solid var(--color-primary);
}
.ingredient-item.checked {
  opacity:.45;
}
.ingredient-item.checked .ingredient-text {
  text-decoration:line-through;
}
.ingredient-check {
  width:22px;
  height:22px;
  display:grid;
  place-items:center;
  flex:0 0 auto;
  border-radius:50%;
  background:var(--gold);
  color:white;
  font-size:.72rem;
  font-weight:800;
  transition:background .2s, opacity .2s;
}
.ingredient-item.checked .ingredient-check {
  background:var(--muted-light);
}
.ingredient-text {
  transition:text-decoration .2s, color .2s;
}
.instruction-list { display:grid; gap:20px; margin:0; padding:0; list-style:none; }
.instruction-list li {
  display:grid;
  grid-template-columns:38px minmax(0, 1fr);
  gap:18px;
  align-items:start;
}
.instruction-list span {
  width:38px;
  height:38px;
  display:grid;
  place-items:center;
  border-radius:50%;
  background:var(--ink);
  color:white;
  font-size:.88rem;
  font-weight:700;
  flex-shrink:0;
}
.instruction-list p,
.notes-box p,
.faq-item p,
.nutrition-note {
  margin:0;
  color:#4a5350;
  font-size:1.05rem;
  line-height:1.68;
}
.instruction-list p { padding-top:8px; }
.tag-list { display:flex; flex-wrap:wrap; gap:8px; padding:36px 0 0; }
.tag-list span {
  min-height:30px;
  display:inline-flex;
  align-items:center;
  padding:0 14px;
  border:1px solid var(--line);
  border-radius:var(--r-pill);
  background:var(--cream);
  color:var(--muted);
  font-size:.82rem;
  font-weight:700;
}
.nutrition-grid {
  display:grid;
  grid-template-columns:repeat(4, minmax(0, 1fr));
  gap:10px;
}
.nutrition-grid div {
  padding:18px 14px;
  border:1px solid var(--line-soft);
  border-radius:var(--r-sm);
  background:var(--cream);
  text-align:center;
}
.nutrition-note { margin-top:14px; font-size:.9rem; font-style:italic; color:var(--muted-light); }
.notes-box {
  display:grid;
  gap:6px;
  padding:20px 22px;
  border-left:3px solid var(--gold);
  border-radius:0 var(--r-sm) var(--r-sm) 0;
  background:var(--gold-pale);
}
.faq-item { padding:18px 0; border-top:1px solid var(--line-soft); }
.faq-item:first-of-type { border-top:0; padding-top:0; }
.faq-item h3 { margin:0 0 8px; font-size:1.02rem; }
.faq-item h3 span { color:var(--gold); }
.faq-item p strong { color:var(--green); }
.comments-section { border-bottom:0; }
.comment-form { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.comment-form textarea, .comment-form button { grid-column:1 / -1; }
.comment-form input, .comment-form textarea {
  width:100%;
  border:1.5px solid var(--line);
  border-radius:var(--r-sm);
  padding:0 14px;
  color:var(--ink);
  font:inherit;
  font-size:.95rem;
  background:white;
  outline:0;
  transition:border-color .18s;
}
.comment-form input:focus, .comment-form textarea:focus { border-color:var(--gold); }
.comment-form input { min-height:46px; }
.comment-form textarea { min-height:130px; padding-top:14px; resize:vertical; }
.comment-form button {
  width:max-content;
  min-height:46px;
  border:0;
  border-radius:var(--r-pill);
  padding:0 28px;
  background:var(--gold);
  color:white;
  font:inherit;
  font-size:.92rem;
  font-weight:700;
  cursor:pointer;
  transition:transform .18s, box-shadow .18s;
}
.comment-form button:hover { transform:translateY(-1px); box-shadow:0 4px 14px rgba(232,160,0,.28); }
.no-comments { margin:14px 0 0; color:var(--muted-light); font-size:.9rem; }

/* ── Footer ───────────────────────────────────────── */
.site-footer {
  width:100%;
  margin:0;
  padding:80px max(28px, calc((100vw - var(--content-max)) / 2 + 28px)) 28px;
  display:grid;
  grid-template-columns:2fr 1fr 1fr 1fr;
  gap:52px;
  color:rgba(255,255,255,0.72);
  background:#2C1910;
  border-top:1px solid rgba(255,255,255,0.08);
}
.footer-brand {
  display:block;
  margin-bottom:10px;
  color:#ffffff;
  font-family:"Bree Serif", Georgia, serif;
  font-size:1.32rem;
  font-weight:700;
  letter-spacing:-.02em;
}
.footer-kicker {
  color:#C96F3D !important;
  font-size:.72rem !important;
  font-weight:800;
  letter-spacing:.18em;
  text-transform:uppercase;
  margin-bottom:12px;
}
.footer-desc {
  max-width:340px;
  color:rgba(255,255,255,0.65);
  font-size:.95rem;
  line-height:1.72;
}
.site-footer h3 {
  margin:0 0 18px;
  color:#ffffff;
  font-family:"Bree Serif", Georgia, serif;
  font-size:1.125rem;
  font-weight:700;
  letter-spacing:-.02em;
  text-transform:none;
}
.site-footer p { max-width:420px; color:rgba(255,255,255,0.65); font-size:.95rem; line-height:1.72; }
.site-footer a { display:block; margin:0 0 6px; color:rgba(255,255,255,0.72); font-family:Lora,"Source Serif 4",Georgia,serif; font-size:1rem; line-height:1.8; transition:color .18s; }
.site-footer a:hover { color:#c96f3d; }
.footer-brand:hover { color:#c96f3d !important; }
.copyright {
  margin:0;
  padding:20px 24px;
  border-top:1px solid rgba(255,255,255,0.08);
  color:rgba(255,255,255,0.4);
  font-size:.82rem;
  text-align:center;
  background:#2C1910;
}

/* ── Responsive Design System (Mobile-First) ──────── */

/* ─────── Extra Small Mobile (320px - 479px) ──────── */
@media (max-width: 479px) {
  /* Base sizing */
  :root { --section-pad:48px 16px; }
  html { font-size:16px; }
  body { font-size:15px; line-height:1.6; }
  
  /* Header & Navigation */
  .site-header { box-shadow:0 1px 0 var(--line); }
  .header-inner { 
    min-height:56px;
    padding:12px 12px;
    grid-template-columns:1fr 40px;
    gap:8px;
  }
  .brand { 
    justify-content:flex-start;
    min-width:0;
    gap:6px;
  }
  .brand-logo { width:36px; height:36px; }
  .brand strong { font-size:1.1rem; }
  .brand-text > span { font-size:.6rem; }
  .site-search { display:none; }
  
  /* Hamburger Menu */
  .nav-toggle {
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    width:40px;
    height:40px;
    border:none;
    background:transparent;
    cursor:pointer;
    gap:4px;
    padding:0;
  }
  .nav-toggle span {
    display:block;
    width:20px;
    height:2px;
    background:var(--ink);
    border-radius:1px;
    transition:all .3s ease;
  }
  .nav-toggle.active span:nth-child(1) {
    transform:rotate(45deg) translate(8px, 8px);
  }
  .nav-toggle.active span:nth-child(2) {
    opacity:0;
  }
  .nav-toggle.active span:nth-child(3) {
    transform:rotate(-45deg) translate(7px, -7px);
  }
  
  nav {
    position:fixed;
    top:56px;
    left:0;
    right:0;
    bottom:0;
    width:100%;
    max-height:0;
    overflow:hidden;
    flex-direction:column;
    justify-content:flex-start;
    background:white;
    border-top:1px solid var(--line);
    gap:0;
    padding:0;
    transition:max-height .3s ease;
    z-index:99;
  }
  nav.active { max-height:calc(100vh - 56px); padding:12px 0; overflow-y:auto; }
  nav a {
    width:100%;
    justify-content:flex-start;
    padding:16px 20px;
    border-radius:0;
    min-height:48px;
    font-size:.95rem;
    border-bottom:1px solid var(--line-soft);
  }
  nav a.active { background:var(--gold-pale); border-left:4px solid var(--gold); }
  
  /* Hero */
  .hero {
    min-height:280px;
    padding:36px 16px 32px;
  }
  .eyebrow { font-size:.7rem; }
  .hero h1 { 
    font-size:clamp(1.5rem, 5vw, 1.8rem);
    margin:12px 0 12px;
  }
  .hero-copy { font-size:.95rem; max-width:100%; }
  .button { 
    padding:0 20px;
    min-height:44px;
    font-size:.9rem;
    width:100%;
    margin-top:20px;
  }
  
  /* Sections */
  .recipe-section { padding:32px 16px; }
  .section-head {
    flex-direction:column;
    gap:12px;
    margin-bottom:20px;
  }
  .section-head h2 {
    font-size:clamp(1.4rem, 5vw, 1.8rem);
  }
  .section-head a { font-size:.85rem; }
  
  /* Cards & Grids */
  .recipe-grid,
  .category-grid {
    grid-template-columns:1fr;
    gap:16px;
  }
  .recipe-card { overflow:visible; }
  .recipe-photo { height:180px; }
  .recipe-card h3 { font-size:1.1rem; }
  .recipe-card p { font-size:.9rem; }
  .recipe-meta { font-size:.8rem; }
  
  /* Chips */
  .chips {
    justify-content:flex-start;
    overflow-x:auto;
    flex-wrap:nowrap;
    -webkit-overflow-scrolling:touch;
    padding:14px 16px;
    gap:6px;
  }
  .chips::-webkit-scrollbar { height:0; }
  .chips a {
    flex:0 0 auto;
    padding:0 12px;
    min-height:36px;
    font-size:.8rem;
  }
  
  /* Newsletter */
  .newsletter {
    padding:40px 16px;
  }
  .newsletter h2 {
    font-size:clamp(1.4rem, 5vw, 1.7rem);
  }
  .newsletter p { font-size:.95rem; }
  .newsletter-form {
    flex-direction:column;
    gap:10px;
    width:100%;
  }
  .newsletter-form input,
  .newsletter-form button {
    width:100%;
    min-height:44px;
  }
  .newsletter-form button { font-size:.9rem; }
  
  /* Chef Card */
  .chef-card {
    grid-template-columns:1fr;
    gap:20px;
    padding:40px 16px;
    text-align:center;
  }
  .chef-photo { 
    max-width:180px;
    margin:0 auto;
    aspect-ratio:1;
  }
  .chef-card h2 { font-size:1.4rem; }
  .chef-card p { font-size:1rem; }
  
  /* Pages */
  .page-hero,
  .page-intro,
  .category-intro {
    padding:28px 16px;
  }
  .page-hero h1,
  .category-hero h1 {
    font-size:clamp(1.5rem, 5vw, 1.8rem);
  }
  
  /* About & Content */
  .about-story {
    grid-template-columns:1fr;
    gap:20px;
    padding:32px 16px;
  }
  .about-photo {
    width:140px;
    margin:0 auto;
  }
  .about-story h2 { font-size:1.5rem; }
  .about-story p { font-size:1rem; }
  
  /* Forms */
  .sidebar-form,
  .contact-form {
    gap:12px;
  }
  .sidebar-form input,
  .contact-form input,
  .contact-form textarea {
    font-size:16px;
    padding:12px 14px;
    min-height:44px;
  }
  .contact-form textarea { min-height:120px; }
  .sidebar-form button,
  .contact-form button {
    width:100%;
    min-height:44px;
    font-size:.9rem;
  }
  .comment-form {
    grid-template-columns:1fr;
  }
  .comment-form input,
  .comment-form textarea {
    font-size:16px;
    min-height:44px;
  }
  .comment-form button { width:100%; }
  
  /* Layouts */
  .category-layout,
  .recipe-layout {
    grid-template-columns:1fr;
    gap:24px;
    padding:28px 16px;
  }
  .category-sidebar,
  .recipe-sidebar {
    position:static;
    width:100%;
  }
  
  /* Recipe Page */
  .recipe-header { padding:8px 0; }
  .recipe-header h1 {
    font-size:clamp(1.5rem, 5vw, 1.8rem);
    line-height:1.1;
    margin:10px 0;
  }
  .recipe-hero-image { 
    aspect-ratio:4/3;
    max-height:240px;
    margin-bottom:20px;
  }
  .article-rating { flex-wrap:wrap; }
  .recipe-summary { font-size:1rem; }
  .recipe-stats {
    grid-template-columns:1fr 1fr;
    gap:8px;
    margin-bottom:32px;
  }
  .recipe-stats div { padding:12px 10px; }
  .recipe-stats strong { font-size:.95rem; }
  .nutrition-grid,
  .ingredient-grid {
    grid-template-columns:1fr;
    gap:8px;
  }
  .ingredient-item {
    min-height:44px;
    padding:10px 12px;
  }
  .instruction-list { gap:16px; }
  .instruction-list li {
    grid-template-columns:32px minmax(0, 1fr);
    gap:12px;
  }
  .instruction-list span {
    width:32px;
    height:32px;
    font-size:.8rem;
  }
  
  /* Sidebar Widgets */
  .sidebar-card { 
    padding:16px 14px;
    margin-bottom:16px;
  }
  .sidebar-card h3 {
    font-size:1rem;
    margin-bottom:12px;
  }
  .sidebar-latest-item,
  .latest-recipe {
    gap:10px;
  }
  .sidebar-latest-thumb,
  .latest-thumb {
    width:60px;
    height:60px;
  }
  
  /* Footer */
  .site-footer {
    grid-template-columns:1fr;
    gap:20px;
    padding:36px 16px;
    text-align:left;
  }
  .footer-brand { margin-bottom:8px; font-size:1.2rem; }
  .footer-desc { max-width:100%; }
  .site-footer h3 { font-size:1rem; margin-bottom:12px; }
  .site-footer a { font-size:.95rem; }
  .copyright { padding:14px 16px; font-size:.75rem; }
}

/* ─────── Small Mobile (480px - 767px) ──────────── */
@media (min-width: 480px) and (max-width: 767px) {
  :root { --section-pad:56px 20px; }
  
  .header-inner {
    min-height:64px;
    padding:12px 20px;
    grid-template-columns:1fr 44px;
  }
  .brand strong { font-size:1.25rem; }
  
  nav { max-height:0; }
  nav.active { max-height:calc(100vh - 64px); }
  
  .hero { padding:48px 20px 40px; }
  .hero h1 { font-size:clamp(1.8rem, 5vw, 2.2rem); }
  
  .recipe-section { padding:40px 20px; }
  .recipe-grid { grid-template-columns:1fr; gap:20px; }
  .recipe-photo { height:220px; }
  
  .chips { padding:16px 20px; }
  .newsletter { padding:48px 20px; }
  .newsletter-form { flex-direction:column; gap:12px; }
  .newsletter-form input,
  .newsletter-form button { width:100%; }
  
  .chef-card { grid-template-columns:1fr; gap:24px; padding:48px 20px; }
  .chef-photo { max-width:220px; margin:0 auto; }
  
  .category-layout,
  .recipe-layout { grid-template-columns:1fr; gap:28px; padding:40px 20px; }
  
  .page-hero { padding:32px 20px; }
  .about-story { grid-template-columns:1fr; gap:24px; padding:40px 20px; }
  .about-photo { width:160px; margin:0 auto; }
  
  .recipe-hero-image { max-height:300px; }
  .recipe-stats { grid-template-columns:repeat(2, 1fr); }
  .nutrition-grid,
  .ingredient-grid { grid-template-columns:1fr; }
  
  .sidebar-card { margin-bottom:16px; }
  .site-footer { grid-template-columns:1fr; gap:24px; padding:44px 20px; }
}

/* ─────── Tablet (768px - 1023px) ────────────────── */
@media (min-width: 768px) and (max-width: 1023px) {
  :root { --section-pad:64px 28px; }
  
  .site-search { display:none; }
  
  .header-inner {
    grid-template-columns:1fr auto;
    gap:20px;
  }
  nav { 
    order:3;
    grid-column:1 / -1;
    justify-content:center;
    padding:12px 0;
    border-top:1px solid var(--line-soft);
  }
  nav a { font-size:.9rem; padding:0 14px; }
  
  .hero { padding:64px 28px 56px; }
  .hero h1 { font-size:clamp(2rem, 4vw, 2.6rem); }
  
  .recipe-section { padding:52px 28px; }
  .recipe-grid { grid-template-columns:repeat(2, 1fr); gap:24px; }
  .recipe-photo { height:220px; }
  
  .category-layout {
    grid-template-columns:1fr;
    gap:36px;
  }
  .category-grid { grid-template-columns:repeat(2, 1fr); gap:20px; }
  .category-sidebar { width:100%; }
  
  .recipe-layout {
    grid-template-columns:1fr;
    gap:32px;
  }
  .recipe-hero-image { max-height:380px; }
  .recipe-stats { grid-template-columns:repeat(3, 1fr); }
  .nutrition-grid,
  .ingredient-grid { grid-template-columns:repeat(2, 1fr); }
  
  .chef-card { grid-template-columns:260px minmax(0, 1fr); gap:40px; }
  
  .newsletter { padding:64px 28px; }
  .newsletter-form { gap:14px; }
  
  .about-story {
    grid-template-columns:200px minmax(0, 1fr);
    gap:40px;
  }
  .about-photo { width:200px; }
  
  .site-footer { gap:36px; padding:64px 28px; }
}

/* ─────── Desktop (1024px+) ────────────────────────── */
@media (min-width: 1024px) {
  nav { 
    order:auto !important;
    grid-column:auto !important;
    position:static !important;
    top:auto !important;
    max-height:none !important;
    overflow:visible !important;
    flex-direction:row !important;
    background:transparent !important;
    border-top:none !important;
    padding:0 !important;
    z-index:auto !important;
  }
  nav a {
    width:auto !important;
    justify-content:auto !important;
    padding:0 14px !important;
    border-radius:var(--r-sm) !important;
    min-height:40px !important;
    border:none !important;
    border-bottom:none !important;
  }
  nav a:hover:not(.active) {
    background:var(--cream);
  }
  
  /* Show desktop elements */
  .site-search { display:flex !important; }
}

/* ═══════════════════════════════════════════════════
   PRINT STYLES — clean recipe card on paper / PDF
   ═══════════════════════════════════════════════════ */
@media print {
  /* ── Hide everything except the recipe article ── */
  .site-header,
  .site-footer,
  .copyright,
  .category-sidebar,
  .recipe-sidebar,
  .chips,
  .article-actions,
  .tag-list,
  .comments-section,
  .newsletter,
  .chef-card,
  .faq-section,
  nav,
  .breadcrumbs {
    display:none !important;
  }

  /* ── Page & body ── */
  @page {
    margin:18mm 16mm;
    size:A4 portrait;
  }
  html, body {
    margin:0;
    padding:0;
    background:#fff;
    color:#111;
    font-size:11pt;
    line-height:1.5;
    font-family:Lora, "Source Serif 4", Georgia, serif;
  }
  h1, h2, h3, h4 { font-family:"Bree Serif", Georgia, serif; }
  a { color:#111; text-decoration:none; }

  /* ── Layout: full-width single column ── */
  .recipe-layout {
    display:block;
    max-width:100%;
    padding:0;
    margin:0;
  }
  .recipe-article {
    width:100%;
    max-width:100%;
  }

  /* ── Recipe header ── */
  .recipe-header {
    border-bottom:2px solid #111;
    padding-bottom:10pt;
    margin-bottom:14pt;
  }
  .eyebrow {
    font-size:8pt;
    letter-spacing:.2em;
    color:#444;
    margin-bottom:4pt;
  }
  .recipe-header h1 {
    font-family:"Bree Serif", Georgia, serif;
    font-size:18pt;
    font-weight:700;
    line-height:1.08;
    margin:4pt 0 8pt;
    letter-spacing:-.01em;
    color:#1f1a16;
  }
  .article-rating {
    font-size:9pt;
    color:#444;
    gap:8pt;
  }
  .article-meta {
    font-size:9pt;
    color:#444;
    margin-top:6pt;
  }

  /* ── Hero image — constrained for paper ── */
  .recipe-hero-image {
    max-height:220pt;
    aspect-ratio:auto;
    border-radius:4pt;
    margin:12pt 0;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
    background-size:cover;
    background-position:center;
  }

  /* ── Recipe intro summary ── */
  .recipe-summary {
    font-size:10.5pt;
    color:#222;
    margin:0 0 14pt;
    line-height:1.6;
  }

  /* ── Stats bar ── */
  .recipe-stats {
    display:grid;
    grid-template-columns:repeat(4, 1fr);
    border:1.5pt solid #ccc;
    border-radius:4pt;
    margin-bottom:18pt;
    page-break-inside:avoid;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
    background:#f9f7f2;
  }
  .recipe-stats div { padding:8pt 10pt; text-align:center; }
  .recipe-stats div + div { border-left:1pt solid #ccc; }
  .recipe-stats span { font-size:7pt; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:#8b8176; display:block; }
  .recipe-stats strong { font-size:10pt; font-weight:700; display:block; margin-top:3pt; color:#2a241f; }

  /* ── Article sections ── */
  .article-section { padding-top:16pt; }
  .article-section h2 {
    font-size:13pt;
    border-bottom:1pt solid #ccc;
    padding-bottom:5pt;
    margin-bottom:10pt;
  }
  .article-section h2::after { display:none; }

  /* ── Ingredients ── */
  .ingredient-grid {
    grid-template-columns:1fr 1fr;
    gap:6pt;
  }
  .ingredient-item {
    font-size:10pt;
    padding:6pt 10pt;
    border:1pt solid #ddd;
    border-radius:3pt;
    min-height:auto;
    background:#fafaf8;
    cursor:default;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
  .ingredient-item.checked {
    opacity:.45;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
  .ingredient-item.checked .ingredient-text {
    text-decoration:line-through;
    color:#777;
  }
  .ingredient-item.checked .ingredient-check {
    background:#aaa;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
  .ingredient-check {
    width:18pt;
    height:18pt;
    font-size:8pt;
    background:#222;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }

  /* ── Instructions ── */
  .instruction-list { gap:10pt; }
  .instruction-list li { grid-template-columns:28pt 1fr; gap:10pt; }
  .instruction-list span {
    width:28pt;
    height:28pt;
    font-size:11pt;
    background:#111;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
  .instruction-list p { font-size:10.5pt; padding-top:4pt; }

  /* ── Nutrition ── */
  .nutrition-grid { grid-template-columns:repeat(4, 1fr); gap:6pt; }
  .nutrition-grid div {
    padding:8pt 6pt;
    border:1pt solid #ddd;
    border-radius:3pt;
    background:#fafaf8;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
  .nutrition-grid span { font-size:7pt; }
  .nutrition-grid strong { font-size:11pt; }
  .nutrition-note { font-size:8pt; color:#666; margin-top:6pt; }

  /* ── Notes box ── */
  .notes-box {
    border-left:3pt solid #999;
    padding:10pt 14pt;
    background:#f9f7f2;
    border-radius:0 3pt 3pt 0;
    -webkit-print-color-adjust:exact;
    print-color-adjust:exact;
  }
  .notes-box p { font-size:10pt; }

  /* ── Page break hints ── */
  .recipe-stats,
  .ingredient-grid,
  .instruction-list { page-break-inside:avoid; }
  .article-section { page-break-before:auto; }
  .article-section:last-of-type { page-break-after:avoid; }

  /* ── Print attribution footer ── */
  .recipe-article::after {
    display:block;
    content:attr(data-site-name);
    margin-top:18pt;
    padding-top:8pt;
    border-top:1pt solid #ddd;
    font-size:8pt;
    color:#888;
    text-align:center;
  }
}
"""


def generate_site(payload: dict, output_root: Path) -> dict:
    website_name = _normalize_site_name((payload.get("website_name") or "").strip() or "Recipe Site")
    chef_name = (payload.get("chef_name") or "").strip() or "Chef"
    uploaded_assets = {
        "chef_image_filename": _uploaded_asset(payload.get("chef_image"), "chef-image"),
        "logo_image_filename": _uploaded_asset(payload.get("logo_image"), "website-logo"),
        "favicon_image_filename": _uploaded_asset(payload.get("favicon_image"), "favicon"),
    }
    site = {
        "website_name": website_name,
        "chef_name": chef_name,
        "siteName": website_name,
        "domain": (payload.get("domain") or slugify(website_name)).strip(),
        "tagline": (payload.get("tagline") or "Simple recipes that work.").strip(),
        "headline": (payload.get("headline") or "Simple Recipes That Work").strip(),
        "hero_text": (payload.get("hero_text") or "Every recipe is tested, practical, and made for real home kitchens.").strip(),
        "about_text": (payload.get("about_text") or f"Hi, I'm {chef_name}. I create simple and comforting recipes that anyone can make at home.").strip(),
        "contact_email": (payload.get("contact_email") or "").strip(),
        "contactEmail": (payload.get("contactEmail") or payload.get("contact_email") or "").strip(),
        "effective_date": (payload.get("effective_date") or payload.get("effectiveDate") or "May 11, 2026").strip(),
        "effectiveDate": (payload.get("effectiveDate") or payload.get("effective_date") or "May 11, 2026").strip(),
        "usesAnalytics": _yes(payload.get("usesAnalytics", payload.get("uses_analytics")), True),
        "usesAds": _yes(payload.get("usesAds", payload.get("uses_ads")), False),
        "usesNewsletter": _yes(payload.get("usesNewsletter", payload.get("uses_newsletter")), True),
        "allowsComments": _yes(payload.get("allowsComments", payload.get("allows_comments")), True),
        "allowsUserContent": _yes(payload.get("allowsUserContent", payload.get("allows_user_content")), False),
        "usesCookies": _yes(payload.get("usesCookies", payload.get("uses_cookies")), True),
        "usesAffiliateLinks": _yes(payload.get("usesAffiliateLinks", payload.get("uses_affiliate_links")), False),
        "hasUserAccounts": _yes(payload.get("hasUserAccounts", payload.get("has_user_accounts")), False),
        "sellsProducts": _yes(payload.get("sellsProducts", payload.get("sells_products")), False),
        "sells_products": _yes(payload.get("sells_products", payload.get("sellsProducts")), False),
        "minimumAge": _minimum_age(payload.get("minimumAge", payload.get("minimum_age", 13))),
        "businessType": (payload.get("businessType") or payload.get("business_type") or "content and recipe blog").strip(),
        "business_type": (payload.get("business_type") or payload.get("businessType") or "content and recipe blog").strip(),
        "country": (payload.get("country") or "United States").strip(),
        "companyName": (payload.get("companyName") or payload.get("company_name") or website_name).strip(),
        "company_name": (payload.get("company_name") or payload.get("companyName") or website_name).strip(),
        "dataControllerName": (payload.get("dataControllerName") or payload.get("data_controller_name") or payload.get("companyName") or payload.get("company_name") or website_name).strip(),
        "data_controller_name": (payload.get("data_controller_name") or payload.get("dataControllerName") or payload.get("company_name") or payload.get("companyName") or website_name).strip(),
        "dataControllerEmail": (payload.get("dataControllerEmail") or payload.get("data_controller_email") or payload.get("contactEmail") or payload.get("contact_email") or "").strip(),
        "data_controller_email": (payload.get("data_controller_email") or payload.get("dataControllerEmail") or payload.get("contact_email") or payload.get("contactEmail") or "").strip(),
        "hasDPO": _yes(payload.get("hasDPO", payload.get("has_dpo")), False),
        "has_dpo": _yes(payload.get("has_dpo", payload.get("hasDPO")), False),
        "dpoEmail": (payload.get("dpoEmail") or payload.get("dpo_email") or "").strip(),
        "dpo_email": (payload.get("dpo_email") or payload.get("dpoEmail") or "").strip(),
        "collectsNames": _yes(payload.get("collectsNames", payload.get("collects_names")), True),
        "collects_names": _yes(payload.get("collects_names", payload.get("collectsNames")), True),
        "collectsEmails": _yes(payload.get("collectsEmails", payload.get("collects_emails")), True),
        "collects_emails": _yes(payload.get("collects_emails", payload.get("collectsEmails")), True),
        "collectsIPAddresses": _yes(payload.get("collectsIPAddresses", payload.get("collects_ip_addresses")), True),
        "collects_ip_addresses": _yes(payload.get("collects_ip_addresses", payload.get("collectsIPAddresses")), True),
        "usesContactForms": _yes(payload.get("usesContactForms", payload.get("uses_contact_forms")), True),
        "uses_contact_forms": _yes(payload.get("uses_contact_forms", payload.get("usesContactForms")), True),
        "legalBasisConsent": _yes(payload.get("legalBasisConsent", payload.get("legal_basis_consent")), True),
        "legal_basis_consent": _yes(payload.get("legal_basis_consent", payload.get("legalBasisConsent")), True),
        "legalBasisLegitimateInterest": _yes(payload.get("legalBasisLegitimateInterest", payload.get("legal_basis_legitimate_interest")), True),
        "legal_basis_legitimate_interest": _yes(payload.get("legal_basis_legitimate_interest", payload.get("legalBasisLegitimateInterest")), True),
        "legalBasisContract": _yes(payload.get("legalBasisContract", payload.get("legal_basis_contract")), False),
        "legal_basis_contract": _yes(payload.get("legal_basis_contract", payload.get("legalBasisContract")), False),
        "legalBasisLegalObligation": _yes(payload.get("legalBasisLegalObligation", payload.get("legal_basis_legal_obligation")), True),
        "legal_basis_legal_obligation": _yes(payload.get("legal_basis_legal_obligation", payload.get("legalBasisLegalObligation")), True),
        "storesDataInEU": _yes(payload.get("storesDataInEU", payload.get("stores_data_in_eu")), True),
        "stores_data_in_eu": _yes(payload.get("stores_data_in_eu", payload.get("storesDataInEU")), True),
        "usesThirdPartyProcessors": _yes(payload.get("usesThirdPartyProcessors", payload.get("uses_third_party_processors")), True),
        "uses_third_party_processors": _yes(payload.get("uses_third_party_processors", payload.get("usesThirdPartyProcessors")), True),
        "affiliatePrograms": _string_list(payload.get("affiliatePrograms", payload.get("affiliate_programs"))),
        "affiliate_programs": _string_list(payload.get("affiliate_programs", payload.get("affiliatePrograms"))),
        "linksToThirdPartySites": _yes(payload.get("linksToThirdPartySites", payload.get("links_to_third_party_sites")), True),
        "links_to_third_party_sites": _yes(payload.get("links_to_third_party_sites", payload.get("linksToThirdPartySites")), True),
        "displaysHealthInfo": _yes(payload.get("displaysHealthInfo", payload.get("displays_health_info")), False),
        "displays_health_info": _yes(payload.get("displays_health_info", payload.get("displaysHealthInfo")), False),
        "displaysNutritionInfo": _yes(payload.get("displaysNutritionInfo", payload.get("displays_nutrition_info")), True),
        "displays_nutrition_info": _yes(payload.get("displays_nutrition_info", payload.get("displaysNutritionInfo")), True),
        "displaysFinancialInfo": _yes(payload.get("displaysFinancialInfo", payload.get("displays_financial_info")), False),
        "displays_financial_info": _yes(payload.get("displays_financial_info", payload.get("displaysFinancialInfo")), False),
        "displaysLegalInfo": _yes(payload.get("displaysLegalInfo", payload.get("displays_legal_info")), False),
        "displays_legal_info": _yes(payload.get("displays_legal_info", payload.get("displaysLegalInfo")), False),
        "displaysTechAdvice": _yes(payload.get("displaysTechAdvice", payload.get("displays_tech_advice")), False),
        "displays_tech_advice": _yes(payload.get("displays_tech_advice", payload.get("displaysTechAdvice")), False),
        "allowsUserGeneratedContent": _yes(payload.get("allowsUserGeneratedContent", payload.get("allows_user_generated_content", payload.get("allowsUserContent", payload.get("allows_user_content")))), False),
        "allows_user_generated_content": _yes(payload.get("allows_user_generated_content", payload.get("allowsUserGeneratedContent", payload.get("allows_user_content", payload.get("allowsUserContent")))), False),
        "publishesProductReviews": _yes(payload.get("publishesProductReviews", payload.get("publishes_product_reviews")), False),
        "publishes_product_reviews": _yes(payload.get("publishes_product_reviews", payload.get("publishesProductReviews")), False),
        "nicheType": (payload.get("nicheType") or payload.get("niche_type") or "recipes").strip(),
        "niche_type": (payload.get("niche_type") or payload.get("nicheType") or "recipes").strip(),
        "privacy_policy": (payload.get("privacy_policy") or "").strip(),
        "terms": (payload.get("terms") or "").strip(),
        "disclaimer": (payload.get("disclaimer") or "").strip(),
        "chef_image_filename": uploaded_assets["chef_image_filename"][0] if uploaded_assets["chef_image_filename"] else "",
        "logo_image_filename": uploaded_assets["logo_image_filename"][0] if uploaded_assets["logo_image_filename"] else "",
        "favicon_image_filename": uploaded_assets["favicon_image_filename"][0] if uploaded_assets["favicon_image_filename"] else "",
    }

    # ── Categories ──────────────────────────────────────────────────────────
    raw_cats = payload.get("categories")
    if raw_cats and isinstance(raw_cats, list):
        site_categories = [c.strip() for c in raw_cats if isinstance(c, str) and c.strip()]
    else:
        niche_key = (payload.get("niche_type") or payload.get("nicheType") or "recipes").lower().strip()
        site_categories = DEFAULT_NICHE_CATEGORIES.get(niche_key, ["Breakfast", "Lunch", "Dinner", "Dessert"])
    site["categories"] = site_categories

    # ── Social links ─────────────────────────────────────────────────────────
    social_links: dict[str, str] = {}
    for platform in ("facebook", "instagram", "pinterest", "twitter", "tiktok", "youtube", "linkedin"):
        url = (payload.get(f"social_{platform}") or "").strip()
        if url:
            social_links[platform] = url
    site["social_links"] = social_links

    # ── Social placement ─────────────────────────────────────────────────────
    social_placement = (payload.get("social_placement") or "footer_only").lower()
    if social_placement not in ("footer_only", "header_only", "both", "hidden"):
        social_placement = "footer_only"
    site["social_placement"] = social_placement

    # ── Theme config ─────────────────────────────────────────────────────────
    raw_theme = payload.get("theme_config") or payload.get("themeConfig")
    if isinstance(raw_theme, dict) and raw_theme:
        site["theme_config"] = raw_theme
    else:
        niche_key = (payload.get("niche_type") or payload.get("nicheType") or "recipes").lower().strip()
        theme_name = NICHE_DEFAULT_THEME.get(niche_key, "Warm Editorial")
        site["theme_config"] = {"name": theme_name, **THEMES[theme_name]}

    slug = slugify(website_name)
    output_dir = output_root / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = {
        PAGE_SLUGS["home"]: _home(site),
        PAGE_SLUGS["about"]: _about_page(site),
        PAGE_SLUGS["privacy"]: _legal_page(site, "privacy_policy", "Privacy Policy", f"{website_name} respects your privacy. This page explains what information may be collected when visitors use the site, including contact form details, analytics data, and basic cookies."),
        PAGE_SLUGS["terms"]: _legal_page(site, "terms", "Terms of Use", f"By using {website_name}, visitors agree to use the recipes and information for personal, lawful purposes. Content may not be copied or republished without permission."),
        PAGE_SLUGS["disclaimer"]: _legal_page(site, "disclaimer", "Disclaimer", f"The recipes and nutrition information on {website_name} are provided for general informational purposes only. Always use your own judgment and follow food-safety guidance."),
    }
    for category in site_categories:
        pages[f"category/{slugify(category)}/index.html"] = _category_page(site, category)
        for title, minutes, description in CATEGORY_RECIPES.get(category, []):
            pages[f"recipe/{slugify(title)}/index.html"] = _recipe_page(site, category, title, minutes, description)

    pages[PAGE_SLUGS["contact"]] = _contact_page(site)

    for filename, content in pages.items():
        path = output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    (output_dir / "style.css").write_text(_style(site), encoding="utf-8")
    base_domain = (payload.get("domain") or slug).strip().rstrip("/")
    if not base_domain.startswith("http"):
        base_domain = f"https://{base_domain}"
    sitemap_urls = [
        f"  <url><loc>{base_domain}/</loc></url>",
        f"  <url><loc>{base_domain}/about.html</loc></url>",
        f"  <url><loc>{base_domain}/contact.html</loc></url>",
        f"  <url><loc>{base_domain}/privacy-policy.html</loc></url>",
        f"  <url><loc>{base_domain}/terms-of-use.html</loc></url>",
        f"  <url><loc>{base_domain}/disclaimer.html</loc></url>",
    ]
    for cat in site_categories:
        cat_slug = slugify(cat)
        sitemap_urls.append(f"  <url><loc>{base_domain}/category/{cat_slug}/</loc></url>")
    for page_path in sorted(pages):
        if page_path.startswith("recipe/"):
            sitemap_urls.append(f"  <url><loc>{base_domain}/{page_path}</loc></url>")
    sitemap_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_urls) + "\n"
        '</urlset>\n'
    )
    (output_dir / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
    api_key_hash = (payload.get("internal_api_key_hash") or payload.get("api_key_hash") or "").strip()
    if api_key_hash:
        api_dir = output_dir / "internal-api" / "publish"
        api_dir.mkdir(parents=True, exist_ok=True)
        (api_dir / "index.php").write_text(_static_publish_api_php(api_key_hash, website_name), encoding="utf-8")

    asset_dir = output_dir / "assets"
    asset_dir.mkdir(exist_ok=True)
    for uploaded in uploaded_assets.values():
        if uploaded:
            filename, data = uploaded
            (asset_dir / filename).write_bytes(data)
    source_asset_dir = Path(__file__).resolve().parents[1] / "assets" / "img"
    for filename in sorted(set(RECIPE_IMAGES.values())):
        source = source_asset_dir / filename
        if source.exists():
            copy2(source, asset_dir / filename)

    return {
        "slug": slug,
        "path": str(output_dir),
        "preview_url": f"/generated-sites/{slug}/index.html",
        "pages": sorted(pages),
    }
