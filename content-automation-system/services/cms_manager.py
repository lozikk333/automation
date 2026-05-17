import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("Africa/Casablanca")
SESSION_COOKIE = "site_owner_session"
SESSION_DAYS = 14
PBKDF2_ITERATIONS = 260_000


def now_iso() -> str:
    return datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "item"


def hash_token(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest_hex = str(stored_hash or "").split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            str(password or "").encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest_hex)
    except Exception:
        return False


def generated_site_slug_from_url(base_url: str) -> str:
    value = str(base_url or "").strip().rstrip("/")
    if "/generated-sites/" in value:
        return value.split("/generated-sites/", 1)[1].strip("/").split("/", 1)[0]
    return slugify(value.rsplit("/", 1)[-1] or value)


def website_by_slug(conn, slug: str):
    base_url = f"/generated-sites/{slugify(slug)}"
    return conn.execute(
        """
        SELECT * FROM websites
        WHERE site_type = 'html_static' AND lower(rtrim(base_url, '/')) = lower(?)
        """,
        (base_url,),
    ).fetchone()


def ensure_unique_slug(conn, table: str, website_id: int, title: str, existing_id: int | None = None) -> str:
    base = slugify(title)
    slug = base
    index = 2
    while True:
        params: list[object] = [website_id, slug]
        query = f"SELECT id FROM {table} WHERE website_id = ? AND slug = ?"
        if existing_id:
            query += " AND id != ?"
            params.append(existing_id)
        if not conn.execute(query, params).fetchone():
            return slug
        slug = f"{base}-{index}"
        index += 1


def public_owner(owner_row) -> dict:
    return {
        "id": owner_row["id"],
        "website_id": owner_row["website_id"],
        "email": owner_row["email"],
        "display_name": owner_row["display_name"],
        "role": owner_row["role"],
    }


def create_owner(conn, website_id: int, email: str, password: str, display_name: str = ""):
    clean_email = str(email or "").strip().lower()
    if not clean_email or "@" not in clean_email:
        raise ValueError("A valid owner email is required")
    if len(str(password or "")) < 10:
        raise ValueError("Owner password must be at least 10 characters")
    now = now_iso()
    conn.execute(
        """
        INSERT INTO site_owners (website_id, email, password_hash, display_name, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(website_id, email) DO UPDATE SET
            password_hash = excluded.password_hash,
            display_name = excluded.display_name,
            updated_at = excluded.updated_at
        """,
        (website_id, clean_email, hash_password(password), display_name or clean_email, now),
    )
    conn.commit()
    return conn.execute(
        "SELECT * FROM site_owners WHERE website_id = ? AND lower(email) = lower(?)",
        (website_id, clean_email),
    ).fetchone()


def ensure_default_cms(conn, website_row, owner_email: str, owner_password: str, display_name: str = ""):
    owner = create_owner(conn, website_row["id"], owner_email, owner_password, display_name)
    settings = {
        "site_title": website_row["name"],
        "tagline": "Simple recipes that work.",
        "logo_url": "",
        "favicon_url": "",
        "theme": "Warm Editorial",
        "primary_color": "#2f6b4f",
        "typography": "System Sans",
        "header_menu": ["Home", "About", "Contact"],
        "footer_content": "",
        "social_links": {},
        "comments_enabled": True,
        "newsletter_enabled": True,
        "seo_title": website_row["name"],
        "seo_description": "",
        "analytics_provider": "",
        "analytics_id": "",
        "custom_header_code": "",
        "custom_footer_code": "",
        "domain": generated_site_slug_from_url(website_row["base_url"]),
        "custom_domain": "",
        "ssl_status": "managed",
        "subdomain": generated_site_slug_from_url(website_row["base_url"]),
        "integrations": {
            "mailchimp": "",
            "resend": "",
            "google_analytics": "",
            "meta_pixel": "",
        },
    }
    now = now_iso()
    for key, value in settings.items():
        conn.execute(
            """
            INSERT OR IGNORE INTO site_settings (website_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (website_row["id"], key, json.dumps(value), now),
        )
    for title, slug, content in [
        ("Home", "home", "Welcome to your CMS-managed homepage."),
        ("About", "about", "Tell readers about this site."),
        ("Contact", "contact", "Add your contact details here."),
    ]:
        conn.execute(
            """
            INSERT OR IGNORE INTO site_pages (website_id, owner_id, title, slug, content, status, updated_at)
            VALUES (?, ?, ?, ?, ?, 'published', ?)
            """,
            (website_row["id"], owner["id"], title, slug, content, now),
        )
    conn.commit()
    return owner


def seed_demo_posts(conn, website_id: int, demo_recipes: dict):
    """Seed demo posts into the database from generated site content.
    
    Args:
        conn: Database connection
        website_id: ID of the website to seed posts for
        demo_recipes: Dictionary of {category: [(title, minutes, description), ...]}
    """
    # Check if posts already exist for this site
    existing = conn.execute(
        "SELECT COUNT(*) as count FROM site_posts WHERE website_id = ?",
        (website_id,)
    ).fetchone()
    
    if existing["count"] > 0:
        return  # Already seeded, skip
    
    now = now_iso()
    rating = "5.0"
    review_count = 125
    
    for category, recipes in demo_recipes.items():
        for title, minutes, description in recipes:
            slug = slugify(title)
            
            # Parse prep/cook time (format: "20 min", "1 hr 30 min")
            prep_time = minutes  # For now, use as prep time
            cook_time = minutes
            
            conn.execute(
                """
                INSERT OR IGNORE INTO site_posts
                (website_id, title, slug, excerpt, content, category, status, 
                 seo_title, meta_description, created_at, updated_at, published_at)
                VALUES (?, ?, ?, ?, ?, ?, 'published', ?, ?, ?, ?, ?)
                """,
                (
                    website_id,
                    title,
                    slug,
                    description[:200],  # excerpt is first 200 chars
                    f"<h2>{escape(title)}</h2><p>{escape(description)}</p><p><strong>Prep Time:</strong> {escape(minutes)}</p>",
                    category,
                    title,  # seo_title
                    description[:160],  # meta_description
                    now,
                    now,
                    now,
                ),
            )
    
    conn.commit()


def authenticate_owner(conn, slug: str, email: str, password: str):
    website = website_by_slug(conn, slug)
    if not website:
        return None, None
    owner = conn.execute(
        "SELECT * FROM site_owners WHERE website_id = ? AND lower(email) = lower(?)",
        (website["id"], str(email or "").strip().lower()),
    ).fetchone()
    if not owner or not verify_password(password, owner["password_hash"]):
        return website, None
    return website, owner


def create_session(conn, website_id: int, owner_id: int) -> tuple[str, str]:
    token = secrets.token_urlsafe(40)
    expires = datetime.now(APP_TIMEZONE) + timedelta(days=SESSION_DAYS)
    conn.execute(
        """
        INSERT INTO site_owner_sessions (owner_id, website_id, token_hash, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (owner_id, website_id, hash_token(token), expires.isoformat(timespec="seconds")),
    )
    conn.commit()
    return token, expires.isoformat(timespec="seconds")


def session_owner(conn, token: str):
    if not token:
        return None
    row = conn.execute(
        """
        SELECT s.id AS session_id, s.expires_at, o.*, w.name AS website_name, w.base_url, w.local_path
        FROM site_owner_sessions s
        JOIN site_owners o ON o.id = s.owner_id AND o.website_id = s.website_id
        JOIN websites w ON w.id = s.website_id
        WHERE s.token_hash = ?
        """,
        (hash_token(token),),
    ).fetchone()
    if not row:
        return None
    expires = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=APP_TIMEZONE)
    if expires < datetime.now(APP_TIMEZONE):
        conn.execute("DELETE FROM site_owner_sessions WHERE id = ?", (row["session_id"],))
        conn.commit()
        return None
    conn.execute("UPDATE site_owner_sessions SET last_seen_at = ? WHERE id = ?", (now_iso(), row["session_id"]))
    conn.commit()
    return row


def logout_session(conn, token: str) -> None:
    if token:
        conn.execute("DELETE FROM site_owner_sessions WHERE token_hash = ?", (hash_token(token),))
        conn.commit()


def require_site_owner(conn, slug: str, token: str):
    website = website_by_slug(conn, slug)
    if not website:
        return None, None
    owner = session_owner(conn, token)
    if not owner or int(owner["website_id"]) != int(website["id"]):
        return website, None
    return website, owner


def settings_dict(conn, website_id: int) -> dict:
    rows = conn.execute("SELECT key, value FROM site_settings WHERE website_id = ?", (website_id,)).fetchall()
    data = {}
    for row in rows:
        try:
            data[row["key"]] = json.loads(row["value"])
        except json.JSONDecodeError:
            data[row["key"]] = row["value"]
    return data


def admin_html(site_name: str) -> str:
    safe_name = escape(site_name or "Site")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_name} Admin</title>
  <link rel="stylesheet" href="/static/site-admin.css?v=20260517-route-fix">
</head>
<body>
  <aside class="cms-sidebar">
    <a class="cms-brand" href="/admin"><strong>{safe_name}</strong><span>CMS Admin</span></a>
    <nav>
      <a href="/admin" data-view="dashboard">Dashboard</a>
      <a href="/admin/posts" data-view="posts">Posts</a>
      <a href="/admin/comments" data-view="comments">Comments</a>
      <a href="/admin/subscribers" data-view="subscribers">Subscribers</a>
      <a href="/admin/media" data-view="media">Media</a>
      <a href="/admin/settings" data-view="settings">Settings</a>
      <a href="/admin/pages" data-view="pages">Pages</a>
      <a href="/admin/analytics" data-view="analytics">Analytics</a>
      <a href="/admin/users" data-view="users">Users</a>
      <a href="/admin/domains" data-view="domains">Domains</a>
      <a href="/admin/appearance" data-view="appearance">Appearance</a>
      <a href="/admin/integrations" data-view="integrations">Integrations</a>
      <a href="/admin/backup-restore" data-view="backup-restore">Backup</a>
    </nav>
    <button id="logout" type="button">Sign out</button>
  </aside>
  <main class="cms-main">
    <header><p id="cms-kicker">Site Admin</p><h1 id="cms-title">Dashboard</h1></header>
    <section id="cms-app"></section>
  </main>
  <script src="/static/site-admin.js?v=20260517-route-fix"></script>
</body>
</html>
"""


def scaffold_admin_files(site_root: str | Path, site_name: str) -> None:
    root = Path(site_root)
    for route in [
        "admin",
        "admin/posts",
        "admin/comments",
        "admin/subscribers",
        "admin/media",
        "admin/settings",
        "admin/pages",
        "admin/analytics",
        "admin/users",
        "admin/domains",
        "admin/appearance",
        "admin/integrations",
        "admin/backup-restore",
    ]:
        target = root / route / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(admin_html(site_name), encoding="utf-8")


def media_upload_path(site_root: str | Path, filename: str) -> tuple[Path, str]:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", filename or "upload.bin").strip("-") or "upload.bin"
    unique = f"{datetime.now(APP_TIMEZONE).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}-{safe}"
    path = Path(site_root) / "uploads" / unique
    return path, f"uploads/{unique}"


def delete_file_if_local(site_root: str | Path, url: str) -> None:
    rel = str(url or "").lstrip("/")
    path = Path(site_root) / rel
    try:
        path.resolve().relative_to(Path(site_root).resolve())
    except ValueError:
        return
    if path.exists() and path.is_file():
        os.remove(path)
