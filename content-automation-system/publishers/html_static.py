"""
HTML static site publisher.

Two publishing modes:
  1. Legacy (contentHtml)  — wraps raw HTML in a minimal page shell.
     Used when article_html artifact is present (backward compatible path).
  2. Recipe JSON            — renders structured recipe data with the premium
     design system. Used for html_static sites via the new HtmlRecipeGenerator
     pipeline. Activated when the payload contains a 'recipeData' key.

WordPress publishing is handled entirely by publishers/wordpress.py.
"""

import hashlib
import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import requests


def token_hash(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or f"article-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _page(title: str, meta_description: str, content_html: str, featured_image: str = "") -> str:
    image = (
        f'<img class="recipe-hero-image" src="{escape(featured_image)}" alt="{escape(title)}">\n'
        if featured_image
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(meta_description or title)}">
  <link rel="stylesheet" href="../../style.css">
</head>
<body>
  <main class="policy-page">
    <article class="article-section">
      <h1>{escape(title)}</h1>
      {image}{content_html}
    </article>
  </main>
</body>
</html>
"""


def publish_to_local_site(site_root: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    root = Path(site_root)
    if not root.exists():
        raise FileNotFoundError(f"Static site path not found: {root}")

    title = str(payload.get("title") or "").strip()
    content_html = str(payload.get("contentHtml") or "").strip()
    if not title or not content_html:
        raise ValueError("title and contentHtml are required")

    slug = slugify(str(payload.get("slug") or title))
    meta_title = str(payload.get("metaTitle") or title).strip()
    meta_description = str(payload.get("metaDescription") or "").strip()
    featured_image = str(payload.get("featuredImage") or "").strip()
    category = str(payload.get("category") or "").strip()
    publish_date = str(payload.get("publishDate") or datetime.utcnow().isoformat()).strip()

    article_path = root / "article" / slug / "index.html"
    _write(article_path, _page(meta_title, meta_description, content_html, featured_image))

    index_path = root / "index.html"
    if index_path.exists():
        index_html = index_path.read_text(encoding="utf-8")
        card = (
            '<article class="recipe-card automation-post">'
            f'<a href="article/{escape(slug)}/">'
            '<div class="recipe-body">'
            f'<p class="eyebrow">{escape(category)}</p>'
            f'<h3>{escape(title)}</h3>'
            f'<p>{escape(meta_description)}</p>'
            f'<div class="recipe-meta"><b>{escape(publish_date)}</b></div>'
            '</div></a></article>'
        )
        marker = "<!-- automation-recent-posts -->"
        if marker in index_html and f'article/{slug}/' not in index_html:
            _write(index_path, index_html.replace(marker, f"{marker}\n{card}", 1))

    sitemap_path = root / "sitemap.xml"
    public_url = f"/article/{slug}/"
    entry = f"  <url><loc>{escape(public_url)}</loc><lastmod>{escape(datetime.utcnow().isoformat())}</lastmod></url>\n"
    if sitemap_path.exists():
        sitemap = sitemap_path.read_text(encoding="utf-8")
        if public_url not in sitemap:
            _write(sitemap_path, sitemap.replace("</urlset>", f"{entry}</urlset>"))
    else:
        _write(
            sitemap_path,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entry}</urlset>\n",
        )

    return {"ok": True, "slug": slug, "url": public_url, "path": str(article_path)}


class HtmlStaticPublisher:
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    def test_connection(self) -> dict[str, Any]:
        response = requests.get(self.endpoint, timeout=20)
        response.raise_for_status()
        return response.json()

    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()


# ===========================================================================
# Premium recipe renderer — html_static / html_recipe_site pipeline only.
# Produces full standalone HTML pages using the same CSS class system as
# services/website_builder.py. Pages link to ../../style.css which must
# exist in the generated site root.
# ===========================================================================

def _stars_html(rating: float) -> str:
    """Render a star rating as accessible HTML."""
    safe = min(5.0, max(0.0, float(rating or 0)))
    label = f"{safe:.1f} out of 5 stars"
    return f'<span class="stars" aria-label="{escape(label)}"></span>'


def _iso_duration(time_str: str) -> str:
    """Convert '35 min' or '1 hr 15 min' to ISO 8601 PT duration."""
    s = (time_str or "").lower()
    hours = int(m.group(1)) if (m := re.search(r"(\d+)\s*h", s)) else 0
    mins  = int(m.group(1)) if (m := re.search(r"(\d+)\s*m", s)) else 0
    total = hours * 60 + mins
    if total <= 0:
        return "PT0M"
    h, m_val = divmod(total, 60)
    return f"PT{h}H{m_val}M" if h else f"PT{m_val}M"


def _json_ld(payload: dict, rd: dict, image_url: str) -> str:
    """Build a Recipe JSON-LD block for the <head>."""
    def _js(v: str) -> str:
        return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

    nutrition = rd.get("nutritionFacts") or {}
    cat = rd.get("selected_category") or {}
    chef = payload.get("chefName") or "Author"
    title = payload.get("title") or ""
    return (
        '  <script type="application/ld+json">\n'
        "  {\n"
        '    "@context": "https://schema.org",\n'
        '    "@type": "Recipe",\n'
        f'    "name": {_js(title)},\n'
        f'    "description": {_js(rd.get("description") or "")},\n'
        f'    "author": {{"@type": "Person", "name": {_js(chef)}}},\n'
        f'    "datePublished": {_js((payload.get("publishDate") or "")[:10])},\n'
        f'    "prepTime": {_js(_iso_duration(rd.get("prepTime", "")))},\n'
        f'    "cookTime": {_js(_iso_duration(rd.get("cookTime", "")))},\n'
        f'    "totalTime": {_js(_iso_duration(rd.get("totalTime", "")))},\n'
        f'    "recipeYield": {_js(rd.get("servings") or "4 servings")},\n'
        f'    "recipeCategory": {_js(cat.get("name") or "")},\n'
        f'    "image": {_js(image_url)},\n'
        f'    "aggregateRating": {{"@type":"AggregateRating","ratingValue":"{rd.get("rating",4.7)}","reviewCount":"{rd.get("ratingCount",0)}"}},\n'
        f'    "nutrition": {{"@type":"NutritionInformation","calories":{_js(nutrition.get("calories",""))},"proteinContent":{_js(nutrition.get("protein",""))},"carbohydrateContent":{_js(nutrition.get("carbs",""))},"fatContent":{_js(nutrition.get("fat",""))}}}\n'
        "  }\n"
        "  </script>\n"
    )


def render_recipe_html(payload: dict) -> str:
    """
    Render the inner article body HTML from a structured recipe payload.

    This is the content-only view (no <html>/<head>/<body> wrapper).
    Used when publishing to remote sites via the PHP endpoint, which wraps
    the content in its own page shell.
    """
    rd: dict = payload.get("recipeData") or {}
    title = escape(payload.get("title") or "")
    category = escape((rd.get("selected_category") or {}).get("name") or payload.get("category") or "")
    chef = escape(payload.get("chefName") or "")
    pub_date = escape((payload.get("publishDate") or "")[:10])
    description = escape(rd.get("description") or "")
    featured_image = payload.get("featuredImage") or ""
    rating = rd.get("rating") or 4.7
    rating_count = rd.get("ratingCount") or 0
    prep = escape(rd.get("prepTime") or "")
    cook = escape(rd.get("cookTime") or "")
    total = escape(rd.get("totalTime") or "")
    servings = escape(rd.get("servings") or "4 servings")

    # Featured image
    hero_img = (
        f'<img class="recipe-hero-image" src="{escape(featured_image)}" '
        f'alt="{title}" style="width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:10px;margin:24px 0">\n'
        if featured_image else
        '<div class="recipe-hero-image photo-fallback" aria-hidden="true" '
        'style="aspect-ratio:16/9;max-height:480px;margin:24px 0"></div>\n'
    )

    # Ingredients
    ingredients_html = "".join(
        f"<li><span>&#10003;</span>{escape(str(item))}</li>"
        for item in (rd.get("ingredients") or [])
    )

    # Instructions
    instructions_html = "".join(
        f"<li><span>{i}</span><p>{escape(str(step))}</p></li>"
        for i, step in enumerate(rd.get("instructions") or [], start=1)
    )

    # Tags
    tags_html = "".join(
        f"<span>{escape(str(t))}</span>"
        for t in (rd.get("tags") or [])
    )

    # Nutrition
    nutrition = rd.get("nutritionFacts") or {}
    nutrition_html = "".join(
        f"<div><span>{escape(label)}</span><strong>{escape(str(nutrition.get(key, '—')))}</strong></div>"
        for label, key in (("Calories", "calories"), ("Protein", "protein"), ("Carbs", "carbs"), ("Fat", "fat"))
    )

    # Notes
    notes_html = "".join(
        f"<p>{escape(str(note))}</p>"
        for note in (rd.get("notes") or [])
    )

    # FAQ
    faq_html = "".join(
        f'<div class="faq-item">'
        f'<h3><span>Q:</span> {escape(str(item.get("question", "")))}</h3>'
        f'<p><strong>A:</strong> {escape(str(item.get("answer", "")))}</p>'
        f'</div>'
        for item in (rd.get("faq") or [])
    )

    notes_section = (
        f'<section class="article-section"><h2>Notes</h2>'
        f'<div class="notes-box">{notes_html}</div></section>'
    ) if notes_html else ""

    faq_section = (
        f'<section class="article-section faq-section"><h2>Frequently Asked Questions</h2>{faq_html}</section>'
    ) if faq_html else ""

    return f"""
<article class="recipe-article">
  <header class="recipe-header">
    <p class="eyebrow">{category}</p>
    <h1>{title}</h1>
    <div class="article-rating">{_stars_html(rating)}<span>{rating:.1f} &nbsp;&middot;&nbsp; {rating_count} ratings</span></div>
    {"<p class='article-meta'>By <strong>" + chef + "</strong> &nbsp;&middot;&nbsp; " + pub_date + "</p>" if chef else ""}
    <div class="article-actions">
      <a class="button" href="#recipe-card">Jump To Recipe &darr;</a>
      <button type="button" onclick="window.print()" aria-label="Print this recipe">&#128424; Print Recipe</button>
    </div>
  </header>
  {hero_img}
  <p class="recipe-summary">{description}</p>
  <div class="recipe-stats" id="recipe-card">
    <div><span>Prep Time</span><strong>{prep}</strong></div>
    <div><span>Cook Time</span><strong>{cook}</strong></div>
    <div><span>Total Time</span><strong>{total}</strong></div>
    <div><span>Servings</span><strong>{servings}</strong></div>
  </div>
  <section class="article-section">
    <h2>Ingredients</h2>
    <ul class="ingredient-grid">{ingredients_html}</ul>
  </section>
  <section class="article-section">
    <h2>Instructions</h2>
    <ol class="instruction-list">{instructions_html}</ol>
  </section>
  {"<div class='tag-list'>" + tags_html + "</div>" if tags_html else ""}
  <section class="article-section">
    <h2>Nutrition Facts</h2>
    <div class="nutrition-grid">{nutrition_html}</div>
    <p class="nutrition-note">* Estimated per serving. Values may vary based on ingredients and preparation.</p>
  </section>
  {notes_section}
  {faq_section}
  <section class="article-section comments-section">
    <h2>Comments</h2>
    <form class="comment-form">
      <input type="text" placeholder="Your name">
      <input type="email" placeholder="your@email.com">
      <textarea placeholder="Share a tip, substitution, or how it turned out..."></textarea>
      <button type="submit">Post Comment</button>
    </form>
    <p class="no-comments">No comments yet &mdash; be the first!</p>
  </section>
</article>
"""


def _recipe_article_page(payload: dict) -> str:
    """
    Render a complete standalone HTML page for a structured recipe.

    Links to ../../style.css (relative path from article/{slug}/index.html
    to the site root). Includes JSON-LD schema in <head> for SEO.
    """
    rd: dict = payload.get("recipeData") or {}
    title = payload.get("title") or ""
    meta_title = payload.get("metaTitle") or title
    meta_desc = payload.get("metaDescription") or rd.get("description") or ""
    featured_image = payload.get("featuredImage") or ""
    schema_block = _json_ld(payload, rd, featured_image)
    body = render_recipe_html(payload)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(meta_title)}</title>
  <meta name="description" content="{escape(meta_desc)}">
{schema_block}  <link rel="stylesheet" href="../../style.css">
</head>
<body>
  <main>
    <div class="recipe-layout" style="grid-template-columns:minmax(0,1fr)">
      {body}
    </div>
  </main>
</body>
</html>
"""


def publish_recipe_to_local_site(site_root: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Publish a structured recipe payload to a local HTML static site.

    Writes:
      article/{slug}/index.html — premium recipe page
      index.html                — injects a recipe card into the post grid
      sitemap.xml               — appends the new URL

    This function is for html_static / html_recipe_site websites only.
    WordPress publishing is handled by publishers/wordpress.py.
    """
    root = Path(site_root)
    if not root.exists():
        raise FileNotFoundError(f"Static site path not found: {root}")

    title = str(payload.get("title") or "").strip()
    rd: dict = payload.get("recipeData") or {}
    if not title:
        raise ValueError("payload.title is required")
    if not rd:
        raise ValueError("payload.recipeData is required")

    slug = slugify(str(payload.get("slug") or title))
    category = str((rd.get("selected_category") or {}).get("name") or payload.get("category") or "").strip()
    meta_description = str(payload.get("metaDescription") or rd.get("description") or "").strip()
    featured_image = str(payload.get("featuredImage") or "").strip()
    publish_date = str(payload.get("publishDate") or datetime.utcnow().isoformat()).strip()
    prep_time = str(rd.get("prepTime") or "").strip()

    # Write the premium recipe page
    article_path = root / "article" / slug / "index.html"
    _write(article_path, _recipe_article_page(payload))

    # Inject a recipe card into the homepage post grid
    index_path = root / "index.html"
    if index_path.exists():
        index_html = index_path.read_text(encoding="utf-8")
        marker = "<!-- automation-recent-posts -->"
        if marker in index_html and f'article/{slug}/' not in index_html:
            img_tag = (
                f'<div class="recipe-photo" style="background-image:url(\'{escape(featured_image)}\')"></div>'
                if featured_image else
                '<div class="recipe-photo photo-fallback"></div>'
            )
            card = (
                '<article class="recipe-card automation-post">'
                f'<a href="article/{escape(slug)}/">'
                f'{img_tag}'
                '<div class="recipe-body">'
                f'<h3>{escape(title)}</h3>'
                f'<p>{escape(meta_description[:120])}{"…" if len(meta_description) > 120 else ""}</p>'
                '<div class="recipe-meta">'
                f'{"<span>&#9719;&nbsp;" + escape(prep_time) + "</span>" if prep_time else ""}'
                f'<span class="stars" aria-hidden="true"></span>'
                '</div>'
                '</div></a></article>'
            )
            _write(index_path, index_html.replace(marker, f"{marker}\n{card}", 1))

    # Append to sitemap
    sitemap_path = root / "sitemap.xml"
    public_url = f"/article/{slug}/"
    entry = (
        f"  <url>"
        f"<loc>{escape(public_url)}</loc>"
        f"<lastmod>{escape(datetime.utcnow().strftime('%Y-%m-%d'))}</lastmod>"
        f"</url>\n"
    )
    if sitemap_path.exists():
        sitemap = sitemap_path.read_text(encoding="utf-8")
        if public_url not in sitemap:
            _write(sitemap_path, sitemap.replace("</urlset>", f"{entry}</urlset>"))
    else:
        _write(
            sitemap_path,
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entry}</urlset>\n",
        )

    return {"ok": True, "slug": slug, "url": public_url, "path": str(article_path)}
