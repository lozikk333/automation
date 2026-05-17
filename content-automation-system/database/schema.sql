-- Main job tracking table
CREATE TABLE IF NOT EXISTS content_jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword     TEXT NOT NULL,
    status      TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'retrying', 'canceled')),
    stage       TEXT CHECK(stage IN (
                    'init', 'research', 'content_generation', 'image_generation',
                    'image_composition', 'wordpress_publish', 'pinterest_metadata',
                    'pinterest_schedule', 'complete'
                )),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_time TIMESTAMP,
    started_at  TIMESTAMP,
    finished_at TIMESTAMP,
    metadata    JSON DEFAULT '{}'
);

-- Intermediate artifacts (URLs, JSON, slugs, etc.)
CREATE TABLE IF NOT EXISTS content_artifacts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         INTEGER NOT NULL,
    artifact_type  TEXT NOT NULL,
    artifact_data  TEXT NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Midjourney task tracking
CREATE TABLE IF NOT EXISTS midjourney_tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     INTEGER NOT NULL,
    task_id    TEXT NOT NULL,
    prompt     TEXT NOT NULL,
    status     TEXT CHECK(status IN ('submitted', 'processing', 'completed', 'failed')),
    image_urls JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- WordPress published posts
CREATE TABLE IF NOT EXISTS wordpress_posts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id         INTEGER NOT NULL,
    wp_post_id     INTEGER NOT NULL,
    title          TEXT NOT NULL,
    slug           TEXT NOT NULL,
    post_url       TEXT NOT NULL,
    featured_media INTEGER,
    status         TEXT DEFAULT 'draft',
    published_at   TIMESTAMP,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Error log for retry tracking
CREATE TABLE IF NOT EXISTS error_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id        INTEGER NOT NULL,
    stage         TEXT,
    error_type    TEXT NOT NULL,
    error_message TEXT NOT NULL,
    retry_count   INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Publishing websites (WordPress and generated/static HTML sites)
CREATE TABLE IF NOT EXISTS websites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    base_url   TEXT NOT NULL,
    site_type  TEXT NOT NULL DEFAULT 'wordpress' CHECK(site_type IN ('wordpress', 'html_static')),
    publish_method TEXT NOT NULL DEFAULT 'wordpress_rest',
    status     TEXT NOT NULL DEFAULT 'active',
    username   TEXT,
    password   TEXT,
    publish_endpoint TEXT,
    api_key_hash TEXT,
    api_enabled INTEGER NOT NULL DEFAULT 0,
    last_publish_at TIMESTAMP,
    local_path TEXT,
    pin_template TEXT NOT NULL DEFAULT 'u1_u2_white_band',
    pin_template_style TEXT,
    categories_json TEXT,
    categories_synced_at TIMESTAMP,
    publish_status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_jobs_status ON content_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_keyword ON content_jobs(keyword);
CREATE INDEX IF NOT EXISTS idx_artifacts_job ON content_artifacts(job_id, artifact_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_websites_base_url_normalized ON websites(lower(rtrim(base_url, '/')));

-- Dashboard logs for the admin UI.
CREATE TABLE IF NOT EXISTS dashboard_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     INTEGER,
    level      TEXT NOT NULL DEFAULT 'info',
    service    TEXT NOT NULL DEFAULT 'system',
    message    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE SET NULL
);

-- Editable prompt templates with simple version history.
CREATE TABLE IF NOT EXISTS dashboard_prompts (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    variables   TEXT DEFAULT '[]',
    content     TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id   TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES dashboard_prompts(id) ON DELETE CASCADE
);

-- General dashboard settings stored as JSON values.
CREATE TABLE IF NOT EXISTS dashboard_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cooperative controls checked by the Celery pipeline between stages.
CREATE TABLE IF NOT EXISTS job_control (
    job_id     INTEGER PRIMARY KEY,
    action     TEXT NOT NULL DEFAULT 'active',
    reason     TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES content_jobs(id) ON DELETE CASCADE
);

-- Optional local API key overrides managed by the dashboard.
CREATE TABLE IF NOT EXISTS api_key_overrides (
    key_id     TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Per-site CMS ownership and content tables. Every row is scoped by website_id
-- so generated sites can share the automation database without sharing data.
CREATE TABLE IF NOT EXISTS site_owners (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id    INTEGER NOT NULL,
    email         TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    display_name  TEXT,
    role          TEXT NOT NULL DEFAULT 'owner',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    UNIQUE (website_id, email)
);

CREATE TABLE IF NOT EXISTS site_owner_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id        INTEGER NOT NULL,
    website_id      INTEGER NOT NULL,
    token_hash      TEXT NOT NULL UNIQUE,
    expires_at      TIMESTAMP NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES site_owners(id) ON DELETE CASCADE,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS site_posts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id       INTEGER NOT NULL,
    owner_id         INTEGER,
    title            TEXT NOT NULL,
    slug             TEXT NOT NULL,
    excerpt          TEXT,
    content          TEXT NOT NULL DEFAULT '',
    category         TEXT,
    tags             TEXT DEFAULT '[]',
    seo_title        TEXT,
    meta_description TEXT,
    status           TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'archived')),
    featured_media_id INTEGER,
    published_at     TIMESTAMP,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES site_owners(id) ON DELETE SET NULL,
    FOREIGN KEY (featured_media_id) REFERENCES site_media(id) ON DELETE SET NULL,
    UNIQUE (website_id, slug)
);

CREATE TABLE IF NOT EXISTS site_pages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER NOT NULL,
    owner_id    INTEGER,
    title       TEXT NOT NULL,
    slug        TEXT NOT NULL,
    content     TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'archived')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES site_owners(id) ON DELETE SET NULL,
    UNIQUE (website_id, slug)
);

CREATE TABLE IF NOT EXISTS site_comments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER NOT NULL,
    post_id     INTEGER,
    author_name TEXT NOT NULL,
    author_email TEXT,
    content     TEXT NOT NULL,
    reply       TEXT,
    status      TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'spam', 'trash')),
    ip_address  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES site_posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS site_subscribers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER NOT NULL,
    email       TEXT NOT NULL,
    name        TEXT,
    status      TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'unsubscribed', 'bounced')),
    source      TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    UNIQUE (website_id, email)
);

CREATE TABLE IF NOT EXISTS site_media (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER NOT NULL,
    owner_id    INTEGER,
    filename    TEXT NOT NULL,
    original_filename TEXT,
    content_type TEXT,
    size_bytes  INTEGER NOT NULL DEFAULT 0,
    url         TEXT NOT NULL,
    alt_text    TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES site_owners(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS site_settings (
    website_id  INTEGER NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (website_id, key),
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS site_activity (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER NOT NULL,
    owner_id    INTEGER,
    action      TEXT NOT NULL,
    entity_type TEXT,
    entity_id   INTEGER,
    message     TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES site_owners(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS site_analytics_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    website_id  INTEGER NOT NULL,
    path        TEXT NOT NULL,
    source      TEXT,
    event_type  TEXT NOT NULL DEFAULT 'page_view',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_site_posts_website_status ON site_posts(website_id, status);
CREATE INDEX IF NOT EXISTS idx_site_pages_website_status ON site_pages(website_id, status);
CREATE INDEX IF NOT EXISTS idx_site_comments_website_status ON site_comments(website_id, status);
CREATE INDEX IF NOT EXISTS idx_site_subscribers_website_status ON site_subscribers(website_id, status);
CREATE INDEX IF NOT EXISTS idx_site_media_website ON site_media(website_id);
CREATE INDEX IF NOT EXISTS idx_site_activity_website ON site_activity(website_id, created_at);
CREATE INDEX IF NOT EXISTS idx_site_analytics_website ON site_analytics_events(website_id, created_at);
