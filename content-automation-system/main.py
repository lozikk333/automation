import json
import math
import os
import re
import shutil
import time
import asyncio
import secrets
import csv
import io
import requests as _requests
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Union
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import CONFIG
from orchestrator.state_manager import JobStatus, Stage, StateManager
from orchestrator.pipeline import schedule_pending_jobs
from publishers.wordpress import WordPressPublisher
from publishers.rss_handler import RSSFeedHandler
from publishers.html_static import HtmlStaticPublisher, token_hash
from services.pin_template_registry import (
    DEFAULT_TEMPLATE_ID,
    apply_pin_template_style,
    extract_pin_template_style,
    get_pin_template_style,
    list_pin_templates,
    load_pin_template,
    update_pin_template_style,
)
from services.pin_template_preview import generate_template_preview
from services.website_builder import generate_site, CATEGORY_RECIPES
from services.cms_manager import (
    SESSION_COOKIE,
    create_owner,
    create_session,
    delete_file_if_local,
    ensure_default_cms,
    ensure_unique_slug,
    generated_site_slug_from_url,
    logout_session,
    media_upload_path,
    public_owner,
    require_site_owner,
    scaffold_admin_files,
    seed_demo_posts,
    settings_dict,
    slugify,
    authenticate_owner,
    hash_password,
    verify_password,
)

BASE_DIR = Path(__file__).resolve().parent
APP_TIMEZONE = ZoneInfo("Africa/Casablanca")

app = FastAPI(title="Choco Kitchen — Content Automation", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/pins", StaticFiles(directory=BASE_DIR / "pins"), name="pins")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")
app.mount("/generated-sites", StaticFiles(directory=BASE_DIR / "generated_sites", html=True), name="generated-sites")

state = StateManager(CONFIG["db_path"])
rss   = RSSFeedHandler(CONFIG["wordpress_url"])


def _check_wordpress_upload_auth(row) -> dict:
    base_url = row["base_url"].rstrip("/")
    auth = (row["username"], row["password"])

    user_resp = _requests.get(
        f"{base_url}/wp-json/wp/v2/users/me?context=edit",
        auth=auth,
        timeout=10,
    )
    if user_resp.status_code == 401:
        return {"ok": False, "status": 401, "message": "Invalid WordPress username or application password"}
    if user_resp.status_code == 403:
        return {"ok": False, "status": 403, "message": "WordPress rejected this user for authenticated REST access"}
    if user_resp.status_code != 200:
        return {"ok": False, "status": user_resp.status_code, "message": f"Authenticated user check failed: HTTP {user_resp.status_code}"}

    user_data = user_resp.json()
    capabilities = user_data.get("capabilities") or {}
    if not capabilities.get("upload_files"):
        return {"ok": False, "status": 403, "message": "This WordPress user cannot upload media. Give the user Author/Editor/Admin permission."}

    return {"ok": True, "status": 200, "message": "Connected — authenticated WordPress user can upload media"}


class GenerateRequest(BaseModel):
    keyword:    Optional[Union[str, List[str]]] = None
    keywords:   Optional[List[str]]             = None
    website_id: Optional[int]                   = None
    batch_name: Optional[str]                   = None
    scheduled_time: Optional[str]               = None
    delay_between_jobs_minutes: Optional[float] = None
    distribution_mode: Optional[str]            = None
    max_jobs_per_day: Optional[int]             = None
    schedule_start_date: Optional[str]          = None
    keywords_per_day: Optional[int]             = None
    delay_between_jobs_hours: Optional[int]     = None
    start_time_each_day: Optional[str]          = None
    timezone: Optional[str]                     = None


class WebsiteCreate(BaseModel):
    name:     str
    base_url: str
    site_type: Optional[str] = "wordpress"
    username: Optional[str] = None
    password: Optional[str] = None
    publish_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_enabled: Optional[bool] = None
    pin_template: Optional[str] = None
    publish_status: Optional[str] = None


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    site_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    publish_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_enabled: Optional[bool] = None
    pin_template: Optional[str] = None
    publish_status: Optional[str] = None


class PromptUpdate(BaseModel):
    content: str


class SettingsUpdate(BaseModel):
    section: str
    value: object


class ApiKeyUpdate(BaseModel):
    value: str


class JobControlRequest(BaseModel):
    reason: Optional[str] = None


class PinTemplateStyleUpdate(BaseModel):
    template_id: Optional[str] = None
    band_background: Optional[str] = None
    font_color: Optional[str] = None
    band_border_color: Optional[str] = None
    band_border_width: Optional[int] = None
    band_radius: Optional[int] = None
    font_family: Optional[str] = None
    font_size_max: Optional[int] = None
    font_size_min: Optional[int] = None
    max_lines: Optional[int] = None
    max_words: Optional[int] = None
    uppercase: Optional[bool] = None
    stroke_fill: Optional[str] = None
    stroke_width: Optional[int] = None
    shadow_fill: Optional[str] = None
    badge_enabled: Optional[bool] = None
    badge_text: Optional[str] = None
    badge_font_family: Optional[str] = None
    badge_background: Optional[str] = None
    badge_fill: Optional[str] = None
    badge_border_color: Optional[str] = None
    badge_font_size: Optional[int] = None
    badge_width: Optional[int] = None
    badge_height: Optional[int] = None
    badge_radius: Optional[int] = None
    accent_enabled: Optional[bool] = None
    accent_text: Optional[str] = None
    accent_fill: Optional[str] = None
    accent_stroke_fill: Optional[str] = None
    accent_font_size: Optional[int] = None


class WebsiteBuilderRequest(BaseModel):
    website_name: str
    chef_name: str
    domain: Optional[str] = None
    tagline: Optional[str] = None
    headline: Optional[str] = None
    hero_text: Optional[str] = None
    about_text: Optional[str] = None
    contact_email: Optional[str] = None
    effective_date: Optional[str] = None
    uses_analytics: Optional[bool] = None
    uses_ads: Optional[bool] = None
    uses_newsletter: Optional[bool] = None
    allows_comments: Optional[bool] = None
    allows_user_content: Optional[bool] = None
    uses_cookies: Optional[bool] = None
    uses_affiliate_links: Optional[bool] = None
    has_user_accounts: Optional[bool] = None
    sells_products: Optional[bool] = None
    minimum_age: Optional[int] = None
    business_type: Optional[str] = None
    country: Optional[str] = None
    company_name: Optional[str] = None
    collects_names: Optional[bool] = None
    collects_emails: Optional[bool] = None
    collects_ip_addresses: Optional[bool] = None
    uses_contact_forms: Optional[bool] = None
    data_controller_name: Optional[str] = None
    data_controller_email: Optional[str] = None
    has_dpo: Optional[bool] = None
    dpo_email: Optional[str] = None
    legal_basis_consent: Optional[bool] = None
    legal_basis_legitimate_interest: Optional[bool] = None
    legal_basis_contract: Optional[bool] = None
    legal_basis_legal_obligation: Optional[bool] = None
    stores_data_in_eu: Optional[bool] = None
    uses_third_party_processors: Optional[bool] = None
    affiliate_programs: Optional[List[str]] = None
    links_to_third_party_sites: Optional[bool] = None
    displays_health_info: Optional[bool] = None
    displays_nutrition_info: Optional[bool] = None
    displays_financial_info: Optional[bool] = None
    displays_legal_info: Optional[bool] = None
    displays_tech_advice: Optional[bool] = None
    allows_user_generated_content: Optional[bool] = None
    publishes_product_reviews: Optional[bool] = None
    niche_type: Optional[str] = None
    legal_preset: Optional[str] = None
    privacy_policy: Optional[str] = None
    terms: Optional[str] = None
    disclaimer: Optional[str] = None
    chef_image: Optional[str] = None
    logo_image: Optional[str] = None
    favicon_image: Optional[str] = None
    # Categories
    categories: Optional[List[str]] = None
    # Social media links
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_pinterest: Optional[str] = None
    social_twitter: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_youtube: Optional[str] = None
    social_linkedin: Optional[str] = None
    social_placement: Optional[str] = None  # footer_only | header_only | both | hidden
    theme_config: Optional[dict] = None     # {name, primary, secondary, accent, ...}
    owner_email: Optional[str] = None
    owner_password: Optional[str] = None


class SiteOwnerLogin(BaseModel):
    email: str
    password: str


class SiteContentPayload(BaseModel):
    title: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = ""
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: Optional[str] = "draft"
    featured_media_id: Optional[int] = None


class CommentModerationPayload(BaseModel):
    status: str
    reply: Optional[str] = None


class SubscriberPayload(BaseModel):
    email: str
    name: Optional[str] = None
    status: Optional[str] = "active"
    source: Optional[str] = "admin"


class OwnerProfilePayload(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None


class PasswordChangePayload(BaseModel):
    current_password: str
    new_password: str


def _style_payload(body: PinTemplateStyleUpdate) -> dict:
    if hasattr(body, "model_dump"):
        return body.model_dump(exclude_unset=True)
    return body.dict(exclude_unset=True)


def _website_style(row) -> dict:
    try:
        return json.loads(row["pin_template_style"] or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}


def _website_categories(row) -> list[dict]:
    try:
        categories = json.loads(row["categories_json"] or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(categories, list):
        return []
    clean = []
    for category in categories:
        if not isinstance(category, dict):
            continue
        try:
            category_id = int(category.get("id"))
        except (TypeError, ValueError):
            continue
        name = str(category.get("name") or "").strip()
        slug = str(category.get("slug") or "").strip()
        if category_id and name and slug:
            clean.append({"id": category_id, "name": name, "slug": slug})
    return clean


def _site_type(row_or_value) -> str:
    if isinstance(row_or_value, str):
        value = row_or_value
    else:
        try:
            value = row_or_value["site_type"]
        except Exception:
            value = ""
    return "html_static" if str(value or "").strip().lower() == "html_static" else "wordpress"


def _publish_method(site_type: str) -> str:
    return "html_static_api" if site_type == "html_static" else "wordpress_rest"


def _public_website(row) -> dict:
    data = dict(row)
    site_type = _site_type(data.get("site_type"))
    categories = _website_categories(data)
    return {
        "id": data["id"],
        "name": data["name"],
        "base_url": data["base_url"],
        "url": data["base_url"],
        "site_type": site_type,
        "siteType": site_type,
        "publish_method": data.get("publish_method") or _publish_method(site_type),
        "publishMethod": data.get("publish_method") or _publish_method(site_type),
        "status": data.get("status") or "active",
        "username": data.get("username") or "",
        "wpUsername": data.get("username") or "",
        "pin_template": data.get("pin_template") or DEFAULT_TEMPLATE_ID,
        "pin_template_style": json.loads(data.get("pin_template_style") or "{}"),
        "publish_status": data.get("publish_status") or "draft",
        "publishEndpoint": data.get("publish_endpoint") or "",
        "publish_endpoint": data.get("publish_endpoint") or "",
        "apiEnabled": bool(data.get("api_enabled")),
        "api_enabled": bool(data.get("api_enabled")),
        "apiKey": "stored securely" if data.get("api_key_hash") else "",
        "lastPublishAt": data.get("last_publish_at"),
        "last_publish_at": data.get("last_publish_at"),
        "categories": categories,
        "category_count": len(categories),
        "categories_synced_at": data.get("categories_synced_at"),
        "created_at": data.get("created_at"),
        "createdAt": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "updatedAt": data.get("updated_at"),
    }


def _normalise_website_url(value: str | None) -> str:
    return str(value or "").strip().rstrip("/").lower()


def _website_by_base_url(base_url: str, exclude_id: int | None = None):
    params: list[object] = [_normalise_website_url(base_url)]
    query = "SELECT * FROM websites WHERE lower(rtrim(base_url, '/')) = ?"
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    return state.conn.execute(query, params).fetchone()


def _sync_wordpress_categories(row) -> tuple[list[dict], str]:
    if _site_type(row) != "wordpress":
        categories = [
            {"id": "breakfast", "name": "Breakfast", "slug": "breakfast"},
            {"id": "lunch", "name": "Lunch", "slug": "lunch"},
            {"id": "dinner", "name": "Dinner", "slug": "dinner"},
            {"id": "dessert", "name": "Dessert", "slug": "dessert"},
        ]
        synced_at = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
        state.conn.execute(
            "UPDATE websites SET categories_json = ?, categories_synced_at = ?, updated_at = ? WHERE id = ?",
            (json.dumps(categories), synced_at, synced_at, row["id"]),
        )
        state.conn.commit()
        return categories, synced_at
    wp = WordPressPublisher(row["base_url"], row["username"], row["password"])
    categories = wp.fetch_categories()
    if not categories:
        raise ValueError("No categories returned from WordPress. Check the site REST API and credentials.")
    synced_at = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    state.conn.execute(
        "UPDATE websites SET categories_json = ?, categories_synced_at = ? WHERE id = ?",
        (json.dumps(categories, ensure_ascii=False), synced_at, row["id"]),
    )
    state.conn.commit()
    return categories, synced_at


def _normalise_casablanca_datetime(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=APP_TIMEZONE)
    return parsed.astimezone(APP_TIMEZONE).isoformat(timespec="minutes")


def _parse_schedule_date(value: str | None, tz: ZoneInfo) -> date:
    if value:
        raw = value.strip()
        if raw:
            if "T" in raw:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=tz)
                return parsed.astimezone(tz).date()
            return date.fromisoformat(raw[:10])
    return datetime.now(tz).date()


def _parse_schedule_time(value: str | None) -> time:
    raw = (value or "08:00").strip()
    if not raw:
        raw = "08:00"
    parts = raw.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("start_time_each_day must be a valid HH:MM time")
    return time(hour=hour, minute=minute)


def _build_auto_day_counts(total_keywords: int, max_jobs_per_day: int | None) -> list[int]:
    if total_keywords <= 0:
        return []
    cap = max_jobs_per_day if max_jobs_per_day and max_jobs_per_day > 0 else 10
    cap = max(1, min(total_keywords, int(cap)))
    days = max(1, math.ceil(total_keywords / cap))
    base = total_keywords // days
    extra = total_keywords % days
    return [base + (1 if index < extra else 0) for index in range(days)]


def _build_keyword_schedule(keywords: list[str], body: GenerateRequest | None) -> list[str | None]:
    mode = (body.distribution_mode or "").strip().lower() if body else ""
    if body and mode == "auto":
        tz = ZoneInfo((body.timezone or "Africa/Casablanca").strip() or "Africa/Casablanca")
        start_date = _parse_schedule_date(body.schedule_start_date or body.scheduled_time, tz)
        start_time = _parse_schedule_time(body.start_time_each_day)
        day_counts = _build_auto_day_counts(len(keywords), body.max_jobs_per_day)
        start_dt = datetime.combine(start_date, start_time, tzinfo=tz)
        scheduled_times: list[str] = []
        for day_offset, count in enumerate(day_counts):
            day_start = start_dt + timedelta(days=day_offset)
            for slot in range(count):
                scheduled_times.append((day_start + timedelta(seconds=slot * 10)).isoformat(timespec="seconds"))
        return scheduled_times

    if not body or body.keywords_per_day is None:
        scheduled = _normalise_casablanca_datetime(body.scheduled_time if body else None)
        return [scheduled for _ in keywords]

    if body.keywords_per_day < 1:
        raise ValueError("keywords_per_day must be at least 1")
    if body.delay_between_jobs_hours not in {0, 1, 2, 3}:
        raise ValueError("delay_between_jobs_hours must be 0, 1, 2, or 3")

    tz = ZoneInfo((body.timezone or "Africa/Casablanca").strip() or "Africa/Casablanca")
    start_date = _parse_schedule_date(body.schedule_start_date or body.scheduled_time, tz)
    start_time = _parse_schedule_time(body.start_time_each_day)
    per_day = max(1, int(body.keywords_per_day))
    delay_hours = int(body.delay_between_jobs_hours)
    if delay_hours == 0:
        per_day = max(per_day, len(keywords))
        delay = timedelta(seconds=10)
    else:
        delay = timedelta(hours=delay_hours)

    scheduled_times: list[str] = []
    for index, _keyword in enumerate(keywords):
        day_offset = index // per_day
        slot = index % per_day
        scheduled_dt = datetime.combine(start_date + timedelta(days=day_offset), start_time, tzinfo=tz) + (delay * slot)
        scheduled_times.append(scheduled_dt.isoformat(timespec="seconds"))
    return scheduled_times


TERMINAL_JOB_STATUSES = {
    JobStatus.COMPLETED.value,
    JobStatus.FAILED.value,
    JobStatus.CANCELED.value,
}


def _require_controllable_job(job_id: int, action: str) -> dict:
    job = state.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] in TERMINAL_JOB_STATUSES:
        raise HTTPException(status_code=409, detail=f"Cannot {action} a {job['status']} job")
    return job


def _session_token(request: Request) -> str:
    return request.cookies.get(SESSION_COOKIE, "")


def _require_cms_owner(slug: str, request: Request):
    website, owner = require_site_owner(state.conn, slug, _session_token(request))
    if not website:
        raise HTTPException(status_code=404, detail="Generated site not found")
    if not owner:
        raise HTTPException(status_code=401, detail="Site owner sign-in required")
    return website, owner


def _row_dict(row) -> dict:
    return dict(row) if row else {}


def _validate_cms_status(status: str, allowed: set[str]) -> str:
    clean = str(status or "").strip().lower()
    if clean not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of: {', '.join(sorted(allowed))}")
    return clean


def _record_site_activity(website_id: int, owner_id: int | None, action: str, entity_type: str, entity_id: int | None, message: str) -> None:
    state.conn.execute(
        """
        INSERT INTO site_activity (website_id, owner_id, action, entity_type, entity_id, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (website_id, owner_id, action, entity_type, entity_id, message, datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")),
    )


def _json_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    try:
        parsed = json.loads(value or "[]")
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass
    return []


def _paginate(page: int, page_size: int) -> tuple[int, int, int]:
    page = max(1, int(page or 1))
    page_size = max(1, min(100, int(page_size or 20)))
    return page, page_size, (page - 1) * page_size


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/jobs-page", include_in_schema=False)
async def jobs_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/new-batch", include_in_schema=False)
async def new_batch_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/websites-page", include_in_schema=False)
async def websites_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/website-builder", include_in_schema=False)
async def website_builder_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/pin-templates-page", include_in_schema=False)
async def pin_templates_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/console", include_in_schema=False)
async def console_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/api-keys-page", include_in_schema=False)
async def api_keys_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/prompts-page", include_in_schema=False)
async def prompts_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/logs-page", include_in_schema=False)
async def logs_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


@app.get("/settings-page", include_in_schema=False)
async def settings_page():
    return FileResponse(BASE_DIR / "static" / "app.html")


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------

@app.post("/generate")
async def generate(
    body: Optional[GenerateRequest] = None,
    keyword: Optional[str] = Query(default=None),
):
    """
    Accepts:
      {"keyword": "chocolate cake"}
      {"keywords": ["chocolate cake", "banana bread", "pancakes"]}
      /generate?keyword=chocolate+cake

    With Celery concurrency=1 each job is processed one by one automatically.
    """
    # Resolve keywords from whichever field was sent
    raw_list: List[str] = []

    if body:
        if body.keywords:
            raw_list = body.keywords
        elif body.keyword:
            kw = body.keyword
            raw_list = [kw] if isinstance(kw, str) else kw
    elif keyword:
        raw_list = [keyword]

    keywords = [kw.strip() for kw in raw_list if kw.strip()]

    if not keywords:
        raise HTTPException(status_code=400, detail="Provide 'keyword' or 'keywords'.")

    if body and body.website_id:
        site_row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (body.website_id,)).fetchone()
        if not site_row:
            raise HTTPException(status_code=404, detail="Selected website was not found.")
        wp_check = _check_wordpress_upload_auth(site_row)
        if not wp_check["ok"]:
            raise HTTPException(
                status_code=400,
                detail=f"Selected website cannot upload WordPress images: {wp_check['message']}",
            )

    try:
        scheduled_times = _build_keyword_schedule(keywords, body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Schedule fields must be valid.")

    if body and body.keywords_per_day is not None:
        settings = state.get_settings()
        execution = dict(settings.get("execution", {}))
        execution["delay_between_jobs_minutes"] = 0
        state.update_settings("execution", execution)
    elif body and body.delay_between_jobs_minutes is not None:
        delay_minutes = max(0, float(body.delay_between_jobs_minutes))
        settings = state.get_settings()
        execution = dict(settings.get("execution", {}))
        execution["delay_between_jobs_minutes"] = delay_minutes
        state.update_settings("execution", execution)

    # Queue every keyword as its own pipeline job
    jobs = []
    print(f"Batch started: {len(keywords)} keyword(s)")

    for kw, scheduled_time in zip(keywords, scheduled_times):
        job_id = state.create_job(
            kw,
            website_id=body.website_id if body else None,
            batch_name=body.batch_name if body else None,
            scheduled_time=scheduled_time,
        )
        jobs.append({"keyword": kw, "job_id": job_id, "status": "pending", "scheduled_time": scheduled_time})
        print(f"  Scheduled job {job_id}: '{kw}'")

    try:
        schedule_pending_jobs()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Celery broker unavailable: {exc}. Start Redis and the worker.",
        )

    print(f"All {len(jobs)} job(s) queued — Celery will process them one by one.")

    # Single keyword: return flat response (backwards-compatible)
    if len(jobs) == 1:
        return {
            "job_id":  jobs[0]["job_id"],
            "keyword": jobs[0]["keyword"],
            "status":  "pending",
            "message": f"Job scheduled for '{jobs[0]['keyword']}'",
        }

    return {
        "total":   len(jobs),
        "status":  "pending",
        "message": f"{len(jobs)} keywords scheduled — scheduler processes one full job at a time",
        "jobs":    jobs,
    }


# ------------------------------------------------------------------
# Status & artifacts
# ------------------------------------------------------------------

@app.get("/status/{job_id}")
async def get_status(job_id: int):
    job = state.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/status")
async def system_status():
    db_ok = True
    try:
        state.conn.execute("SELECT 1").fetchone()
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        import redis
        redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"), socket_connect_timeout=1).ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    celery_ok = False
    try:
        from orchestrator.pipeline import app as celery_app
        celery_ok = bool(celery_app.control.inspect(timeout=1).ping() or {})
    except Exception:
        celery_ok = False

    usage = shutil.disk_usage(".")
    return {
        "celery_status": "online" if celery_ok else "offline",
        "redis_status": "online" if redis_ok else "offline",
        "db_status": "online" if db_ok else "offline",
        "resource_usage": {
            "disk_total": usage.total,
            "disk_used": usage.used,
            "disk_free": usage.free,
            "cpu": None,
            "memory": None,
        },
        "current_jobs": len([j for j in state.list_jobs(limit=100) if j["status"] in ("processing", "retrying")]),
        "queued_jobs": len([j for j in state.list_jobs(limit=100) if j["status"] == "pending"]),
    }


@app.get("/jobs")
async def list_jobs(status: str = None, limit: int = 20):
    """List recent jobs, optionally filtered by status."""
    return {"jobs": state.list_jobs(status=status, limit=limit)}


@app.get("/jobs/{job_id}")
async def get_job(job_id: int):
    job = state.get_job_detail(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs/{job_id}/pause")
async def pause_job(job_id: int, body: Optional[JobControlRequest] = None):
    _require_controllable_job(job_id, "pause")
    state.set_job_control(job_id, "paused", body.reason if body else None)
    return {"ok": True, "job_id": job_id, "action": "paused"}


@app.post("/jobs/{job_id}/resume")
async def resume_job(job_id: int, body: Optional[JobControlRequest] = None):
    _require_controllable_job(job_id, "resume")
    state.set_job_control(job_id, "active", body.reason if body else None)
    return {"ok": True, "job_id": job_id, "action": "active"}


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: int, body: Optional[JobControlRequest] = None):
    _require_controllable_job(job_id, "cancel")
    state.set_job_control(job_id, "cancel_requested", body.reason if body else None)
    state.update_job(job_id, status=JobStatus.CANCELED, metadata={"control_state": "canceled"})
    return {"ok": True, "job_id": job_id, "action": "canceled", "status": "canceled"}


@app.post("/jobs/{job_id}/retry")
async def retry_job(job_id: int, body: Optional[JobControlRequest] = None):
    original = state.get_job_status(job_id)
    if not original:
        raise HTTPException(status_code=404, detail="Job not found")
    if original["status"] in {JobStatus.PENDING.value, JobStatus.PROCESSING.value, JobStatus.RETRYING.value}:
        raise HTTPException(status_code=409, detail="Job is already queued or running")

    retry_requested_at = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    metadata = dict(original.get("metadata") or {})
    metadata.update(
        {
            "scheduler_managed": True,
            "manual_retry": True,
            "retry_reason": body.reason if body else None,
            "retry_requested_at": retry_requested_at,
            "previous_status": original["status"],
        }
    )
    state.conn.execute("DELETE FROM error_log WHERE job_id = ?", (job_id,))
    state.conn.execute("DELETE FROM content_artifacts WHERE job_id = ?", (job_id,))
    state.conn.execute("DELETE FROM midjourney_tasks WHERE job_id = ?", (job_id,))
    state.conn.execute("DELETE FROM wordpress_posts WHERE job_id = ?", (job_id,))
    state.conn.execute("DELETE FROM job_control WHERE job_id = ?", (job_id,))
    state.conn.execute(
        """
        UPDATE content_jobs
        SET status = ?,
            stage = ?,
            updated_at = ?,
            scheduled_time = NULL,
            started_at = NULL,
            finished_at = NULL,
            celery_task_id = NULL,
            metadata = ?
        WHERE id = ?
        """,
        (
            JobStatus.PENDING.value,
            Stage.INIT.value,
            retry_requested_at,
            json.dumps(metadata),
            job_id,
        ),
    )
    state.conn.commit()
    state.log_dashboard(job_id, "info", "api", f"Retry queued for same job #{job_id}")
    schedule_pending_jobs()
    return {"ok": True, "job_id": job_id, "status": "pending", "same_job": True}


@app.get("/stats")
async def stats():
    return state.get_stats()


@app.get("/logs")
async def logs(job_id: Optional[int] = None, level: Optional[str] = None, limit: int = 200):
    return {"logs": state.get_logs(job_id=job_id, level=level, limit=limit)}


@app.get("/artifacts/{job_id}")
async def get_artifacts(job_id: int):
    if not state.get_job_status(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    cursor = state.conn.execute(
        "SELECT artifact_type, artifact_data FROM content_artifacts WHERE job_id = ? ORDER BY id",
        (job_id,),
    )
    artifacts = {}
    for row in cursor.fetchall():
        key, val = row[0], row[1]
        try:
            artifacts[key] = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            artifacts[key] = val

    return {"job_id": job_id, "artifacts": artifacts}


# ------------------------------------------------------------------
# Websites
# ------------------------------------------------------------------

@app.get("/websites")
async def list_websites():
    cursor = state.conn.execute(
        "SELECT * FROM websites ORDER BY id DESC"
    )
    rows = [_public_website(r) for r in cursor.fetchall()]
    return {"websites": rows}


@app.get("/pin-templates")
async def pin_templates():
    return {"default": DEFAULT_TEMPLATE_ID, "templates": list_pin_templates()}


@app.get("/pin-templates/{template_id}/style")
async def pin_template_style(template_id: str):
    try:
        return get_pin_template_style(template_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.put("/pin-templates/{template_id}/style")
async def update_pin_template_colors(template_id: str, body: PinTemplateStyleUpdate):
    try:
        style = update_pin_template_style(
            template_id,
            band_background=body.band_background,
            font_color=body.font_color,
            band_border_color=body.band_border_color,
            band_border_width=body.band_border_width,
            band_radius=body.band_radius,
            font_family=body.font_family,
            font_size_max=body.font_size_max,
            font_size_min=body.font_size_min,
            max_lines=body.max_lines,
            max_words=body.max_words,
            uppercase=body.uppercase,
            stroke_fill=body.stroke_fill,
            stroke_width=body.stroke_width,
            shadow_fill=body.shadow_fill,
            badge_enabled=body.badge_enabled,
            badge_text=body.badge_text,
            badge_font_family=body.badge_font_family,
            badge_background=body.badge_background,
            badge_fill=body.badge_fill,
            badge_border_color=body.badge_border_color,
            badge_font_size=body.badge_font_size,
            badge_width=body.badge_width,
            badge_height=body.badge_height,
            badge_radius=body.badge_radius,
            accent_enabled=body.accent_enabled,
            accent_text=body.accent_text,
            accent_fill=body.accent_fill,
            accent_stroke_fill=body.accent_stroke_fill,
            accent_font_size=body.accent_font_size,
        )
        generate_template_preview(template_id, force=True)
        return style
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/pin-templates/{template_id}/preview", include_in_schema=False)
async def pin_template_preview(template_id: str, refresh: bool = Query(default=False)):
    try:
        path = generate_template_preview(template_id, force=refresh)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Preview unavailable: {exc}")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/websites/{website_id}/pin-template-style")
async def website_pin_template_style(website_id: int):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    try:
        merged = apply_pin_template_style(load_pin_template(row["pin_template"]), _website_style(row))
        return extract_pin_template_style(merged)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.put("/websites/{website_id}/pin-template-style")
async def update_website_pin_template_style(website_id: int, body: PinTemplateStyleUpdate):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    try:
        template_id = (body.template_id or row["pin_template"] or DEFAULT_TEMPLATE_ID).strip()
        style = _style_payload(body)
        merged = apply_pin_template_style(load_pin_template(template_id), style)
        state.conn.execute(
            "UPDATE websites SET pin_template = ?, pin_template_style = ? WHERE id = ?",
            (template_id, json.dumps(style), website_id),
        )
        state.conn.commit()
        generate_template_preview(
            template_id,
            force=True,
            style_override=style,
            cache_key=f"website_{website_id}",
        )
        return extract_pin_template_style(merged)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/websites/{website_id}/pin-template-preview", include_in_schema=False)
async def website_pin_template_preview(website_id: int, refresh: bool = Query(default=False)):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    try:
        path = generate_template_preview(
            row["pin_template"],
            force=refresh,
            style_override=_website_style(row),
            cache_key=f"website_{website_id}",
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Preview unavailable: {exc}")
    return FileResponse(path, media_type="image/jpeg")


@app.post("/websites", status_code=201)
async def create_website(body: WebsiteCreate):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    base_url = body.base_url.strip().rstrip("/")
    if not base_url.startswith("http"):
        raise HTTPException(status_code=400, detail="base_url must be a valid URL starting with http")
    site_type = _site_type(body.site_type or "wordpress")
    username = (body.username or "").strip()
    password = (body.password or "").strip()
    publish_endpoint = (body.publish_endpoint or f"{base_url}/internal-api/publish/").strip().rstrip("/")
    api_key = (body.api_key or "").strip()
    if site_type == "wordpress":
        if not username:
            raise HTTPException(status_code=400, detail="username is required")
        if not password:
            raise HTTPException(status_code=400, detail="password is required")
        api_key_hash = None
        api_enabled = 0
        publish_endpoint = None
    else:
        if not api_key:
            api_key = secrets.token_urlsafe(32)
        api_key_hash = token_hash(api_key)
        api_enabled = 1 if body.api_enabled is not False else 0
        username = ""
        # Stored for automated outbound publishing. The API key hash is the
        # value used for validation, listing, and generated site configuration.
        password = api_key

    pin_template = (body.pin_template or DEFAULT_TEMPLATE_ID).strip()
    publish_status = (body.publish_status or "draft").strip().lower()
    if publish_status not in {"draft", "publish"}:
        raise HTTPException(status_code=400, detail="publish_status must be draft or publish")
    existing = _website_by_base_url(base_url)
    if existing:
        state.conn.execute(
            """
            UPDATE websites
            SET name = ?, base_url = ?, site_type = ?, publish_method = ?, status = 'active',
                username = ?, password = ?, publish_endpoint = ?, api_key_hash = ?,
                api_enabled = ?, pin_template = ?, publish_status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                body.name.strip(), base_url, site_type, _publish_method(site_type), username, password,
                publish_endpoint, api_key_hash, api_enabled, pin_template, publish_status,
                datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"), existing["id"],
            ),
        )
        state.conn.commit()
        row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (existing["id"],)).fetchone()
        categories = _website_categories(row)
        state.log_dashboard(None, "info", "websites", f"Website updated without duplicate: {body.name.strip()}")
        return {
            "id": existing["id"],
            "name": body.name.strip(),
            "base_url": base_url,
            **_public_website(row),
            "categories": categories,
            "category_count": len(categories),
            "categories_sync_error": None,
            "api_key": api_key if site_type == "html_static" else "",
        }
    cursor = state.conn.execute(
        """
        INSERT INTO websites
            (name, base_url, site_type, publish_method, status, username, password,
             publish_endpoint, api_key_hash, api_enabled, pin_template, publish_status, updated_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            body.name.strip(), base_url, site_type, _publish_method(site_type), username, password,
            publish_endpoint, api_key_hash, api_enabled, pin_template, publish_status,
            datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
        ),
    )
    state.conn.commit()
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (cursor.lastrowid,)).fetchone()
    categories = []
    categories_synced_at = None
    categories_sync_error = None
    try:
        categories, categories_synced_at = _sync_wordpress_categories(row)
        state.log_dashboard(None, "info", "websites", f"Synced {len(categories)} categories for website: {body.name.strip()}")
    except Exception as exc:
        categories_sync_error = str(exc)
        state.log_dashboard(None, "warn", "websites", f"Category sync failed for {body.name.strip()}: {exc}")
    return {
        **_public_website(row),
        "categories": categories,
        "category_count": len(categories),
        "categories_synced_at": categories_synced_at,
        "categories_sync_error": categories_sync_error,
        "api_key": api_key if site_type == "html_static" else "",
    }


@app.put("/websites/{website_id}")
async def update_website(website_id: int, body: WebsiteUpdate):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    data = dict(row)
    body_data = body.model_dump(exclude_unset=True) if hasattr(body, "model_dump") else body.dict(exclude_unset=True)
    name = (body.name if body.name is not None else data["name"]).strip()
    base_url = (body.base_url if body.base_url is not None else data["base_url"]).strip().rstrip("/")
    site_type = _site_type(body.site_type if body.site_type is not None else data.get("site_type"))
    username = (body.username if body.username is not None else data.get("username") or "").strip()
    password = (body.password if "password" in body_data else data.get("password") or "").strip()
    publish_endpoint = (body.publish_endpoint if body.publish_endpoint is not None else data.get("publish_endpoint") or f"{base_url}/internal-api/publish/").strip().rstrip("/")
    api_enabled = (1 if body.api_enabled else 0) if body.api_enabled is not None else int(data.get("api_enabled") or 0)
    api_key_hash = data.get("api_key_hash")
    if body.api_key:
        password = body.api_key.strip()
        api_key_hash = token_hash(password)
    pin_template = (body.pin_template if body.pin_template is not None else data.get("pin_template") or DEFAULT_TEMPLATE_ID).strip()
    publish_status = (body.publish_status if body.publish_status is not None else data.get("publish_status") or "draft").strip().lower()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    if not base_url.startswith("http"):
        raise HTTPException(status_code=400, detail="base_url must start with http")
    if site_type == "wordpress":
        if not username or not password:
            raise HTTPException(status_code=400, detail="username and password are required")
        publish_endpoint = None
        api_key_hash = None
        api_enabled = 0
    else:
        username = ""
        if not password:
            generated = secrets.token_urlsafe(32)
            password = generated
            api_key_hash = token_hash(generated)
        if not api_key_hash:
            api_key_hash = token_hash(password)
        if not publish_endpoint:
            publish_endpoint = f"{base_url}/internal-api/publish"
    if publish_status not in {"draft", "publish"}:
        raise HTTPException(status_code=400, detail="publish_status must be draft or publish")
    duplicate = _website_by_base_url(base_url, exclude_id=website_id)
    if duplicate:
        raise HTTPException(status_code=409, detail="Another website already uses this base_url")
    state.conn.execute(
        """
        UPDATE websites
        SET name = ?, base_url = ?, site_type = ?, publish_method = ?, username = ?, password = ?,
            publish_endpoint = ?, api_key_hash = ?, api_enabled = ?, pin_template = ?,
            publish_status = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            name, base_url, site_type, _publish_method(site_type), username, password, publish_endpoint,
            api_key_hash, api_enabled, pin_template, publish_status,
            datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"), website_id,
        ),
    )
    state.conn.commit()
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    categories = _website_categories(row)
    categories_sync_error = None
    if body.base_url is not None or body.username is not None or body.password is not None:
        try:
            categories, _ = _sync_wordpress_categories(row)
            state.log_dashboard(None, "info", "websites", f"Synced {len(categories)} categories for website: {name}")
        except Exception as exc:
            categories_sync_error = str(exc)
            state.log_dashboard(None, "warn", "websites", f"Category sync failed for {name}: {exc}")
    state.log_dashboard(None, "info", "websites", f"Website updated: {name}")
    return {
        **_public_website(row),
        "categories": categories,
        "category_count": len(categories),
        "categories_sync_error": categories_sync_error,
        "api_key": body.api_key if site_type == "html_static" and body.api_key else "",
    }


@app.post("/websites/{website_id}/sync-categories")
async def sync_website_categories(website_id: int):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    if _site_type(row) != "wordpress":
        categories, synced_at = _sync_wordpress_categories(row)
        return {
            "ok": True,
            "website_id": website_id,
            "categories": categories,
            "category_count": len(categories),
            "categories_synced_at": synced_at,
            "message": f"Synced {len(categories)} static categories.",
        }
    try:
        categories, synced_at = _sync_wordpress_categories(row)
    except Exception as exc:
        state.log_dashboard(None, "warn", "websites", f"Category sync failed for {row['name']}: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    state.log_dashboard(None, "info", "websites", f"Synced {len(categories)} categories for website: {row['name']}")
    return {
        "ok": True,
        "website_id": website_id,
        "categories": categories,
        "category_count": len(categories),
        "categories_synced_at": synced_at,
        "message": f"Synced {len(categories)} categories.",
    }


@app.post("/websites/{website_id}/test")
async def test_website(website_id: int):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    if _site_type(row) == "html_static":
        if row["local_path"] and Path(row["local_path"]).exists():
            return {"ok": True, "message": "Local static site folder is available for publishing"}
        if not row["publish_endpoint"] or not row["password"]:
            return {"ok": False, "message": "HTML static publish endpoint or API key is missing"}
        try:
            return HtmlStaticPublisher(row["publish_endpoint"], row["password"]).test_connection()
        except Exception as e:
            return {"ok": False, "message": str(e)}
    try:
        return _check_wordpress_upload_auth(row)
    except Exception as e:
        return {"ok": False, "message": str(e)}


@app.post("/websites/{website_id}/regenerate-api-key")
async def regenerate_website_api_key(website_id: int):
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    if _site_type(row) != "html_static":
        raise HTTPException(status_code=400, detail="API key regeneration is only available for HTML static websites")
    api_key = secrets.token_urlsafe(32)
    api_key_hash = token_hash(api_key)
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    state.conn.execute(
        "UPDATE websites SET password = ?, api_key_hash = ?, api_enabled = 1, updated_at = ? WHERE id = ?",
        (api_key, api_key_hash, now, website_id),
    )
    state.conn.commit()
    local_path = row["local_path"] if "local_path" in row.keys() else ""
    if local_path:
        api_path = Path(local_path) / "internal-api" / "publish" / "index.php"
        if api_path.exists():
            api_text = api_path.read_text(encoding="utf-8")
            api_text = re.sub(
                r"const AUTOMATION_API_KEY_HASH = '[^']*';",
                f"const AUTOMATION_API_KEY_HASH = '{api_key_hash}';",
                api_text,
            )
            api_path.write_text(api_text, encoding="utf-8")
    state.log_dashboard(None, "info", "websites", f"Regenerated HTML static API key for {row['name']}")
    return {"ok": True, "api_key": api_key, "api_key_hash": api_key_hash}


@app.delete("/websites/{website_id}", status_code=200)
async def delete_website(website_id: int):
    row = state.conn.execute("SELECT id FROM websites WHERE id = ?", (website_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Website not found")
    state.conn.execute("DELETE FROM websites WHERE id = ?", (website_id,))
    state.conn.commit()
    return {"deleted": website_id}


# ------------------------------------------------------------------
# API Keys — status + test
# ------------------------------------------------------------------

def _mask(value: str) -> str:
    """Return a masked version: first 6 chars + *** + last 4 chars."""
    if not value:
        return ""
    if len(value) <= 10:
        return "***"
    return value[:6] + "•" * 6 + value[-4:]


def _api_key_value(key_id: str, env_var: str) -> str:
    return state.get_api_key_override(key_id) or os.getenv(env_var, "")


def _google_credentials_path():
    return __import__("pathlib").Path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"))


@app.get("/api-keys")
async def get_api_keys():
    """Return configured keys (masked) with their current status."""
    llm_key     = _api_key_value("nvidia", "OPENROUTER_API_KEY")
    ttapi_key   = _api_key_value("ttapi", "TTAPI_API_KEY")
    sheet_name  = _api_key_value("sheets", "GOOGLE_SHEET_NAME")
    creds_exist = _google_credentials_path().exists()

    return {
        "keys": [
            {
                "id":          "nvidia",
                "service":     "OpenRouter (LLM)",
                "description": "Generates article content and image prompts",
                "env_var":     "OPENROUTER_API_KEY",
                "masked":      _mask(llm_key),
                "configured":  bool(llm_key),
            },
            {
                "id":          "ttapi",
                "service":     "TTAPI (Midjourney)",
                "description": "Generates food photography images via Midjourney",
                "env_var":     "TTAPI_API_KEY",
                "masked":      _mask(ttapi_key),
                "configured":  bool(ttapi_key),
            },
            {
                "id":          "sheets",
                "service":     "Google Sheets",
                "description": "Logs published articles to a spreadsheet",
                "env_var":     "GOOGLE_SHEET_NAME",
                "masked":      sheet_name if sheet_name else "",
                "configured":  bool(sheet_name) and creds_exist,
                "extra":       {
                    "sheet_name":    sheet_name,
                    "creds_present": creds_exist,
                },
            },
            {
                "id":          "wordpress",
                "service":     "WordPress REST API",
                "description": "Publishes articles and uploads media",
                "env_var":     "WORDPRESS_APP_PASSWORD",
                "masked":      _mask(_api_key_value("wordpress", "WORDPRESS_APP_PASSWORD")),
                "configured":  bool(_api_key_value("wordpress", "WORDPRESS_APP_PASSWORD")),
                "extra":       {
                    "url":      os.getenv("WORDPRESS_URL",      ""),
                    "username": os.getenv("WORDPRESS_USERNAME", ""),
                },
            },
        ]
    }


@app.put("/api-keys/{key_id}")
async def update_api_key(key_id: str, body: ApiKeyUpdate):
    known = {"nvidia", "ttapi", "sheets", "wordpress"}
    if key_id not in known:
        raise HTTPException(status_code=404, detail=f"Unknown key id: {key_id}")
    state.set_api_key_override(key_id, body.value)
    return {"ok": True, "id": key_id, "masked": _mask(body.value)}


@app.post("/api-keys/test/{key_id}")
async def test_api_key(key_id: str):
    """Live-test each configured integration."""

    if key_id == "nvidia":
        api_key = _api_key_value("nvidia", "OPENROUTER_API_KEY")
        if not api_key:
            return {"ok": False, "message": "OPENROUTER_API_KEY not set in .env"}
        try:
            resp = _requests.post(
                os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://127.0.0.1:8011"),
                    "X-OpenRouter-Title": os.getenv("OPENROUTER_APP_NAME", "Content Automation"),
                },
                json={
                    "model": os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it:free"),
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 5,
                    "temperature": 0.15,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "stream": False,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return {"ok": True, "message": "Connected — OpenRouter API responded successfully"}
            if resp.status_code == 401:
                return {"ok": False, "message": "Invalid API key (401 Unauthorized)"}
            return {"ok": False, "message": f"Unexpected response: HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "message": f"Connection error: {e}"}

    if key_id == "ttapi":
        api_key = _api_key_value("ttapi", "TTAPI_API_KEY")
        if not api_key:
            return {"ok": False, "message": "TTAPI_API_KEY not set in .env"}
        try:
            ttapi_base = os.getenv("TTAPI_BASE_URL", "https://hold.ttapi.io/midjourney/v1").rstrip("/")
            resp = _requests.get(
                f"{ttapi_base}/fetch",
                headers={"TT-API-KEY": api_key},
                params={"jobId": "ping"},
                timeout=10,
            )
            # 400/404 with a JSON body = API reached and key was accepted
            if resp.status_code in (200, 400, 404):
                return {"ok": True, "message": "Connected — TTAPI (Midjourney) key is valid"}
            if resp.status_code == 401:
                return {"ok": False, "message": "Invalid API key (401 Unauthorized)"}
            return {"ok": False, "message": f"Unexpected response: HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "message": f"Connection error: {e}"}

    if key_id == "sheets":
        creds_path = _google_credentials_path()
        if not creds_path.exists():
            return {"ok": False, "message": "Google credentials not found"}
        sheet_name = os.getenv("GOOGLE_SHEET_NAME", "")
        if not sheet_name:
            return {"ok": False, "message": "GOOGLE_SHEET_NAME not set in .env"}
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            creds  = Credentials.from_service_account_file(
                str(creds_path),
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"],
            )
            client = gspread.authorize(creds)
            client.open(sheet_name)
            return {"ok": True, "message": f"Connected — sheet \"{sheet_name}\" found and accessible"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    if key_id == "wordpress":
        wp_url  = os.getenv("WORDPRESS_URL",          "")
        wp_user = os.getenv("WORDPRESS_USERNAME",      "")
        wp_pass = _api_key_value("wordpress", "WORDPRESS_APP_PASSWORD")
        if not all([wp_url, wp_user, wp_pass]):
            return {"ok": False, "message": "WordPress credentials incomplete in .env"}
        try:
            resp = _requests.get(
                wp_url.rstrip("/") + "/wp-json/wp/v2/posts?per_page=1",
                auth=(wp_user, wp_pass),
                timeout=10,
            )
            if resp.status_code == 200:
                return {"ok": True, "message": f"Connected — WordPress REST API at {wp_url}"}
            if resp.status_code == 401:
                return {"ok": False, "message": "Invalid credentials (401 Unauthorized)"}
            return {"ok": False, "message": f"Unexpected response: HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "message": f"Connection error: {e}"}

    raise HTTPException(status_code=404, detail=f"Unknown key id: {key_id}")


@app.get("/prompts")
async def get_prompts():
    return {"prompts": state.get_prompts()}


@app.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, body: PromptUpdate):
    row = state.update_prompt(prompt_id, body.content)
    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found")
    item = dict(row)
    item["variables"] = json.loads(item["variables"] or "[]")
    return item


@app.get("/prompts/{prompt_id}/history")
async def prompt_history(prompt_id: str):
    return {"history": state.get_prompt_history(prompt_id)}


@app.post("/prompts/{prompt_id}/test")
async def test_prompt(prompt_id: str, sample: dict):
    prompt = next((p for p in state.get_prompts() if p["id"] == prompt_id), None)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    output = prompt["content"]
    for key, value in sample.items():
        output = output.replace("{" + key + "}", str(value))
    return {"ok": True, "output": output}


@app.get("/settings")
async def get_settings():
    return {"settings": state.get_settings()}


@app.put("/settings")
async def update_settings(body: SettingsUpdate):
    if body.section == "execution" and isinstance(body.value, dict):
        body.value["worker_concurrency"] = 1
    return {"settings": state.update_settings(body.section, body.value)}


# ---------------------------------------------------------------------------
# Legal preset system
# ---------------------------------------------------------------------------

def _base_legal() -> dict:
    return {
        "collects_names": True, "collects_emails": True, "collects_ip_addresses": True,
        "uses_cookies": True, "uses_analytics": True, "uses_newsletter": True,
        "uses_contact_forms": True, "allows_comments": True, "uses_ads": False,
        "uses_affiliate_links": False, "allows_user_content": False,
        "allows_user_generated_content": False, "has_user_accounts": False,
        "sells_products": False, "publishes_product_reviews": False,
        "displays_health_info": False, "displays_financial_info": False,
        "displays_tech_advice": False, "displays_nutrition_info": False,
        "displays_legal_info": False, "links_to_third_party_sites": True,
        "legal_basis_consent": True, "legal_basis_legitimate_interest": True,
        "legal_basis_contract": False, "legal_basis_legal_obligation": True,
        "stores_data_in_eu": False, "uses_third_party_processors": True,
        "has_dpo": False, "dpo_email": "", "data_controller_name": "",
        "data_controller_email": "", "minimum_age": 13,
        "business_type": "content blog", "country": "United States",
    }


LEGAL_PRESETS: dict[str, dict] = {
    "content_blog": {
        "label": "Content Blog Default",
        **_base_legal(),
    },
    "recipe_blog": {
        "label": "Recipe Blog Default",
        **_base_legal(),
        "displays_nutrition_info": True, "uses_affiliate_links": True,
        "business_type": "recipe and food blog",
    },
    "affiliate_blog": {
        "label": "Affiliate Blog Default",
        **_base_legal(),
        "uses_ads": True, "uses_affiliate_links": True, "publishes_product_reviews": True,
        "links_to_third_party_sites": True, "business_type": "affiliate and review blog",
    },
    "health_blog": {
        "label": "Health Blog Default",
        **_base_legal(),
        "displays_health_info": True, "displays_nutrition_info": True,
        "business_type": "health and wellness blog",
    },
    "finance_blog": {
        "label": "Finance Blog Default",
        **_base_legal(),
        "displays_financial_info": True, "displays_legal_info": True,
        "business_type": "personal finance blog",
    },
    "tech_blog": {
        "label": "Tech Blog Default",
        **_base_legal(),
        "displays_tech_advice": True, "uses_affiliate_links": True,
        "business_type": "technology blog",
    },
    "eu_gdpr": {
        "label": "EU GDPR Default",
        **_base_legal(),
        "stores_data_in_eu": True, "has_dpo": True,
        "legal_basis_consent": True, "legal_basis_legitimate_interest": True,
        "legal_basis_legal_obligation": True,
        "country": "European Union",
    },
    "us_standard": {
        "label": "US Standard Default",
        **_base_legal(),
        "stores_data_in_eu": False, "country": "United States",
        "legal_basis_consent": True,
    },
}

NICHE_TO_PRESET: dict[str, str] = {
    "recipes": "recipe_blog",
    "health": "health_blog",
    "fitness": "health_blog",
    "finance": "finance_blog",
    "technology": "tech_blog",
    "product reviews": "affiliate_blog",
}


def _resolve_legal_preset(preset_id: str) -> dict:
    """Return preset fields, merged with any user-saved customisations."""
    base = {k: v for k, v in LEGAL_PRESETS.get(preset_id, LEGAL_PRESETS["content_blog"]).items() if k != "label"}
    row = state.conn.execute(
        "SELECT value FROM dashboard_settings WHERE key = ?",
        (f"legal_preset_{preset_id}",),
    ).fetchone()
    if row:
        try:
            base.update(json.loads(row["value"]))
        except Exception:
            pass
    return base


@app.get("/settings/legal-presets")
async def get_legal_presets():
    result = {}
    for pid, pdef in LEGAL_PRESETS.items():
        fields = {k: v for k, v in pdef.items() if k != "label"}
        row = state.conn.execute(
            "SELECT value FROM dashboard_settings WHERE key = ?",
            (f"legal_preset_{pid}",),
        ).fetchone()
        if row:
            try:
                fields.update(json.loads(row["value"]))
            except Exception:
                pass
        result[pid] = {"label": pdef["label"], **fields}
    return {"presets": result}


@app.put("/settings/legal-presets/{preset_id}")
async def update_legal_preset(preset_id: str, request: Request):
    if preset_id not in LEGAL_PRESETS:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset_id}")
    body = await request.json()
    # Only store fields that differ from the base definition
    value = json.dumps(body)
    state.conn.execute(
        """
        INSERT INTO dashboard_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        (f"legal_preset_{preset_id}", value, datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")),
    )
    state.conn.commit()
    state.log_dashboard(None, "info", "settings", f"Legal preset '{preset_id}' updated")
    return {"ok": True, "preset_id": preset_id}


# Keep backward-compat endpoint — returns content_blog preset
@app.get("/settings/website-defaults")
async def get_website_defaults():
    return {"defaults": _resolve_legal_preset("content_blog")}


@app.put("/settings/website-defaults")
async def update_website_defaults(request: Request):
    body = await request.json()
    value = json.dumps(body)
    state.conn.execute(
        """
        INSERT INTO dashboard_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        ("legal_preset_content_blog", value, datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")),
    )
    state.conn.commit()
    return {"defaults": body}


@app.post("/website-builder/generate")
async def generate_website(body: WebsiteBuilderRequest):
    if not body.website_name.strip():
        raise HTTPException(status_code=400, detail="Website name is required")
    if not body.chef_name.strip():
        raise HTTPException(status_code=400, detail="Chef name is required")
    output_root = BASE_DIR / "generated_sites"
    api_key = secrets.token_urlsafe(32)
    api_key_hash = token_hash(api_key)

    # Resolve legal preset: explicit > named preset (+ niche auto-select) > content_blog base
    niche = (body.niche_type or "").lower().strip()
    preset_id = body.legal_preset or NICHE_TO_PRESET.get(niche, "content_blog")
    if preset_id == "custom":
        # Use individual fields from request as-is; fall back to content_blog for missing ones
        preset = _resolve_legal_preset("content_blog")
    else:
        preset = _resolve_legal_preset(preset_id)

    # body fields that were explicitly set (non-None) override the preset
    explicit = {k: v for k, v in body.model_dump().items() if v is not None and k not in ("legal_preset",)}
    payload = {**preset, **explicit}
    payload["internal_api_key_hash"] = api_key_hash
    try:
        result = generate_site(payload, output_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    base_url = f"/generated-sites/{result['slug']}"
    publish_endpoint = f"{base_url}/internal-api/publish"
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    existing = _website_by_base_url(base_url)
    if existing:
        website_id = existing["id"]
        state.conn.execute(
            """
            UPDATE websites
            SET name = ?, base_url = ?, site_type = 'html_static', publish_method = 'html_static_api',
                status = 'active', username = '', password = ?, publish_endpoint = ?, api_key_hash = ?,
                api_enabled = 1, local_path = ?, pin_template = ?, publish_status = 'publish', updated_at = ?
            WHERE id = ?
            """,
            (body.website_name.strip(), base_url, api_key, publish_endpoint, api_key_hash, result["path"], DEFAULT_TEMPLATE_ID, now, website_id),
        )
    else:
        cursor = state.conn.execute(
            """
            INSERT INTO websites
                (name, base_url, site_type, publish_method, status, username, password,
                 publish_endpoint, api_key_hash, api_enabled, local_path, pin_template, publish_status, updated_at)
            VALUES (?, ?, 'html_static', 'html_static_api', 'active', '', ?, ?, ?, 1, ?, ?, 'publish', ?)
            """,
            (body.website_name.strip(), base_url, api_key, publish_endpoint, api_key_hash, result["path"], DEFAULT_TEMPLATE_ID, now),
        )
        website_id = cursor.lastrowid
    state.conn.commit()
    row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
    owner_email = (body.owner_email or body.contact_email or f"owner@{result['slug']}.local").strip().lower()
    owner_password = body.owner_password or secrets.token_urlsafe(14)
    try:
        ensure_default_cms(state.conn, row, owner_email, owner_password, body.chef_name.strip())
        seed_demo_posts(state.conn, website_id, CATEGORY_RECIPES)
        scaffold_admin_files(result["path"], body.website_name.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    state.log_dashboard(None, "info", "website_builder", f"Generated website preview: {result['slug']}")
    return {
        "ok": True,
        **result,
        "website": _public_website(row),
        "api_key": api_key,
        "publish_endpoint": publish_endpoint,
        "admin_url": f"/generated-sites/{result['slug']}/admin/",
        "owner": {"email": owner_email, "password": owner_password},
    }


# ════════════════════════════════════════════════════════════════════════════════
# PUBLIC API ENDPOINTS — Frontend Post Fetching
# ════════════════════════════════════════════════════════════════════════════════

def _get_site_by_slug(slug: str):
    """Get website by slug without requiring auth."""
    return state.conn.execute("SELECT * FROM websites WHERE base_url LIKE ?", (f"%{slug}%",)).fetchone()


@app.get("/api/v1/sites/{slug}/posts")
async def api_get_posts(
    slug: str,
    category: str = "",
    status: str = "published",
    page: int = 1,
    page_size: int = 20,
):
    """Get published posts for a site (public endpoint for frontend)."""
    website = _get_site_by_slug(slug)
    if not website:
        raise HTTPException(status_code=404, detail="Site not found")
    
    query = "SELECT * FROM site_posts WHERE website_id = ? AND status = ?"
    params = [website["id"], status or "published"]
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY published_at DESC, created_at DESC"
    
    offset = (page - 1) * page_size
    query += f" LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    
    posts = state.conn.execute(query, params).fetchall()
    
    # Get total count
    count_query = "SELECT COUNT(*) as count FROM site_posts WHERE website_id = ? AND status = ?"
    count_params = [website["id"], status or "published"]
    if category:
        count_query += " AND category = ?"
        count_params.append(category)
    
    total = state.conn.execute(count_query, count_params).fetchone()["count"]
    
    return {
        "ok": True,
        "posts": [_row_dict(row) for row in posts],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
    }


@app.get("/api/v1/sites/{slug}/posts/{post_id}")
async def api_get_post(slug: str, post_id: int):
    """Get a single published post (public endpoint)."""
    website = _get_site_by_slug(slug)
    if not website:
        raise HTTPException(status_code=404, detail="Site not found")
    
    post = state.conn.execute(
        "SELECT * FROM site_posts WHERE id = ? AND website_id = ? AND status = 'published'",
        (post_id, website["id"]),
    ).fetchone()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"ok": True, "post": _row_dict(post)}


@app.get("/api/v1/sites/{slug}/categories")
async def api_get_categories(slug: str):
    """Get all categories with post counts (public endpoint)."""
    website = _get_site_by_slug(slug)
    if not website:
        raise HTTPException(status_code=404, detail="Site not found")
    
    categories = state.conn.execute(
        """
        SELECT DISTINCT category, COUNT(*) as count
        FROM site_posts
        WHERE website_id = ? AND status = 'published' AND category IS NOT NULL
        GROUP BY category
        ORDER BY category
        """,
        (website["id"],),
    ).fetchall()
    
    return {
        "ok": True,
        "categories": [{"name": row["category"], "count": row["count"]} for row in categories],
    }


@app.post("/cms/sites/{slug}/auth/login")
async def cms_login(slug: str, body: SiteOwnerLogin, response: Response):
    website, owner = authenticate_owner(state.conn, slug, body.email, body.password)
    if not website:
        raise HTTPException(status_code=404, detail="Generated site not found")
    if not owner:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, expires_at = create_session(state.conn, website["id"], owner["id"])
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=14 * 24 * 60 * 60,
        path=f"/cms/sites/{slug}",
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=14 * 24 * 60 * 60,
        path=f"/generated-sites/{slug}/admin",
    )
    return {"ok": True, "expires_at": expires_at, "owner": public_owner(owner)}


@app.post("/cms/sites/{slug}/auth/logout")
async def cms_logout(slug: str, request: Request, response: Response):
    logout_session(state.conn, _session_token(request))
    response.delete_cookie(SESSION_COOKIE, path=f"/cms/sites/{slug}")
    response.delete_cookie(SESSION_COOKIE, path=f"/generated-sites/{slug}/admin")
    return {"ok": True}


@app.get("/cms/sites/{slug}/auth/me")
async def cms_me(slug: str, request: Request):
    website, owner = _require_cms_owner(slug, request)
    return {"website": _public_website(website), "owner": public_owner(owner)}


@app.get("/cms/sites/{slug}/summary")
async def cms_summary(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    wid = website["id"]
    counts = {
        "posts": state.conn.execute("SELECT COUNT(*) AS count FROM site_posts WHERE website_id = ?", (wid,)).fetchone()["count"],
        "published_posts": state.conn.execute("SELECT COUNT(*) AS count FROM site_posts WHERE website_id = ? AND status = 'published'", (wid,)).fetchone()["count"],
        "pending_comments": state.conn.execute("SELECT COUNT(*) AS count FROM site_comments WHERE website_id = ? AND status = 'pending'", (wid,)).fetchone()["count"],
        "subscribers": state.conn.execute("SELECT COUNT(*) AS count FROM site_subscribers WHERE website_id = ?", (wid,)).fetchone()["count"],
        "media": state.conn.execute("SELECT COUNT(*) AS count FROM site_media WHERE website_id = ?", (wid,)).fetchone()["count"],
        "pages": state.conn.execute("SELECT COUNT(*) AS count FROM site_pages WHERE website_id = ?", (wid,)).fetchone()["count"],
    }
    activity = state.conn.execute(
        "SELECT * FROM site_activity WHERE website_id = ? ORDER BY created_at DESC LIMIT 8",
        (wid,),
    ).fetchall()
    latest_comments = state.conn.execute(
        """
        SELECT c.*, p.title AS post_title
        FROM site_comments c
        LEFT JOIN site_posts p ON p.id = c.post_id AND p.website_id = c.website_id
        WHERE c.website_id = ?
        ORDER BY c.created_at DESC LIMIT 5
        """,
        (wid,),
    ).fetchall()
    latest_subscribers = state.conn.execute(
        "SELECT * FROM site_subscribers WHERE website_id = ? ORDER BY created_at DESC LIMIT 5",
        (wid,),
    ).fetchall()
    return {
        **counts,
        "activity": [_row_dict(row) for row in activity],
        "latest_comments": [_row_dict(row) for row in latest_comments],
        "latest_subscribers": [_row_dict(row) for row in latest_subscribers],
        "quick_actions": [
            {"label": "New post", "view": "posts"},
            {"label": "Upload media", "view": "media"},
            {"label": "Edit settings", "view": "settings"},
        ],
    }


def _list_site_content(
    table: str,
    website_id: int,
    search: str = "",
    status: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20,
):
    clauses = ["website_id = ?"]
    params: list[object] = [website_id]
    if search:
        clauses.append("(lower(title) LIKE ? OR lower(content) LIKE ? OR lower(slug) LIKE ?)")
        needle = f"%{search.lower()}%"
        params.extend([needle, needle, needle])
    if status:
        clauses.append("status = ?")
        params.append(status)
    if table == "site_posts" and category:
        clauses.append("category = ?")
        params.append(category)
    where = " AND ".join(clauses)
    page, page_size, offset = _paginate(page, page_size)
    total = state.conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE {where}", params).fetchone()["count"]
    rows = state.conn.execute(
        f"SELECT * FROM {table} WHERE {where} ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?",
        (*params, page_size, offset),
    ).fetchall()
    items = []
    for row in rows:
        data = _row_dict(row)
        if "tags" in data:
            data["tags"] = _json_list(data.get("tags"))
        items.append(data)
    return {"items": items, "page": page, "page_size": page_size, "total": total, "pages": max(1, math.ceil(total / page_size))}


def _create_site_content(table: str, website_id: int, owner_id: int, body: SiteContentPayload):
    status = _validate_cms_status(body.status or "draft", {"draft", "published", "archived"})
    slug = slugify(body.slug or body.title)
    slug = ensure_unique_slug(state.conn, table, website_id, slug)
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    if table == "site_posts":
        cursor = state.conn.execute(
            """
            INSERT INTO site_posts
                (website_id, owner_id, title, slug, excerpt, content, category, tags,
                 seo_title, meta_description, status, featured_media_id, published_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                website_id,
                owner_id,
                body.title.strip(),
                slug,
                body.excerpt or "",
                body.content or "",
                body.category or "",
                json.dumps(body.tags or []),
                body.seo_title or body.title.strip(),
                body.meta_description or "",
                status,
                body.featured_media_id,
                now if status == "published" else None,
                now,
            ),
        )
    else:
        cursor = state.conn.execute(
            """
            INSERT INTO site_pages (website_id, owner_id, title, slug, content, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (website_id, owner_id, body.title.strip(), slug, body.content or "", status, now),
        )
    _record_site_activity(website_id, owner_id, "created", "post" if table == "site_posts" else "page", cursor.lastrowid, f"Created {body.title.strip()}")
    state.conn.commit()
    return _row_dict(state.conn.execute(f"SELECT * FROM {table} WHERE id = ?", (cursor.lastrowid,)).fetchone())


def _update_site_content(table: str, website_id: int, item_id: int, body: SiteContentPayload):
    existing = state.conn.execute(f"SELECT * FROM {table} WHERE id = ? AND website_id = ?", (item_id, website_id)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    status = _validate_cms_status(body.status or existing["status"], {"draft", "published", "archived"})
    slug = slugify(body.slug or existing["slug"] or body.title)
    slug = ensure_unique_slug(state.conn, table, website_id, slug, existing_id=item_id)
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    if table == "site_posts":
        published_at = existing["published_at"] or (now if status == "published" else None)
        state.conn.execute(
            """
            UPDATE site_posts
            SET title = ?, slug = ?, excerpt = ?, content = ?, category = ?, tags = ?,
                seo_title = ?, meta_description = ?, status = ?, featured_media_id = ?,
                published_at = ?, updated_at = ?
            WHERE id = ? AND website_id = ?
            """,
            (
                body.title.strip(),
                slug,
                body.excerpt or "",
                body.content or "",
                body.category or "",
                json.dumps(body.tags or []),
                body.seo_title or body.title.strip(),
                body.meta_description or "",
                status,
                body.featured_media_id,
                published_at,
                now,
                item_id,
                website_id,
            ),
        )
    else:
        state.conn.execute(
            """
            UPDATE site_pages
            SET title = ?, slug = ?, content = ?, status = ?, updated_at = ?
            WHERE id = ? AND website_id = ?
            """,
            (body.title.strip(), slug, body.content or "", status, now, item_id, website_id),
        )
    _record_site_activity(website_id, None, "updated", "post" if table == "site_posts" else "page", item_id, f"Updated {body.title.strip()}")
    state.conn.commit()
    data = _row_dict(state.conn.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone())
    if "tags" in data:
        data["tags"] = _json_list(data.get("tags"))
    return data


@app.get("/cms/sites/{slug}/posts")
async def cms_posts(
    slug: str,
    request: Request,
    search: str = "",
    status: str = "",
    category: str = "",
    page: int = 1,
    page_size: int = 20,
):
    website, _owner = _require_cms_owner(slug, request)
    return _list_site_content("site_posts", website["id"], search, status, category, page, page_size)


@app.post("/cms/sites/{slug}/posts", status_code=201)
async def cms_create_post(slug: str, body: SiteContentPayload, request: Request):
    website, owner = _require_cms_owner(slug, request)
    return {"item": _create_site_content("site_posts", website["id"], owner["id"], body)}


@app.put("/cms/sites/{slug}/posts/{post_id}")
async def cms_update_post(slug: str, post_id: int, body: SiteContentPayload, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    return {"item": _update_site_content("site_posts", website["id"], post_id, body)}


@app.delete("/cms/sites/{slug}/posts/{post_id}")
async def cms_delete_post(slug: str, post_id: int, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    state.conn.execute("DELETE FROM site_posts WHERE id = ? AND website_id = ?", (post_id, website["id"]))
    _record_site_activity(website["id"], None, "deleted", "post", post_id, "Deleted post")
    state.conn.commit()
    return {"ok": True}


@app.post("/cms/sites/{slug}/posts/{post_id}/duplicate", status_code=201)
async def cms_duplicate_post(slug: str, post_id: int, request: Request):
    website, owner = _require_cms_owner(slug, request)
    row = state.conn.execute("SELECT * FROM site_posts WHERE id = ? AND website_id = ?", (post_id, website["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    title = f"{row['title']} Copy"
    slug_value = ensure_unique_slug(state.conn, "site_posts", website["id"], title)
    cursor = state.conn.execute(
        """
        INSERT INTO site_posts
            (website_id, owner_id, title, slug, excerpt, content, category, tags,
             seo_title, meta_description, status, featured_media_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
        """,
        (
            website["id"],
            owner["id"],
            title,
            slug_value,
            row["excerpt"],
            row["content"],
            row["category"],
            row["tags"],
            row["seo_title"],
            row["meta_description"],
            row["featured_media_id"],
            now,
        ),
    )
    _record_site_activity(website["id"], owner["id"], "duplicated", "post", cursor.lastrowid, f"Duplicated {row['title']}")
    state.conn.commit()
    return {"item": _row_dict(state.conn.execute("SELECT * FROM site_posts WHERE id = ?", (cursor.lastrowid,)).fetchone())}


@app.get("/cms/sites/{slug}/pages")
async def cms_pages(slug: str, request: Request, search: str = "", status: str = "", page: int = 1, page_size: int = 20):
    website, _owner = _require_cms_owner(slug, request)
    return _list_site_content("site_pages", website["id"], search, status, "", page, page_size)


@app.post("/cms/sites/{slug}/pages", status_code=201)
async def cms_create_page(slug: str, body: SiteContentPayload, request: Request):
    website, owner = _require_cms_owner(slug, request)
    return {"item": _create_site_content("site_pages", website["id"], owner["id"], body)}


@app.put("/cms/sites/{slug}/pages/{page_id}")
async def cms_update_page(slug: str, page_id: int, body: SiteContentPayload, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    return {"item": _update_site_content("site_pages", website["id"], page_id, body)}


@app.delete("/cms/sites/{slug}/pages/{page_id}")
async def cms_delete_page(slug: str, page_id: int, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    state.conn.execute("DELETE FROM site_pages WHERE id = ? AND website_id = ?", (page_id, website["id"]))
    _record_site_activity(website["id"], None, "deleted", "page", page_id, "Deleted page")
    state.conn.commit()
    return {"ok": True}


@app.get("/cms/sites/{slug}/comments")
async def cms_comments(slug: str, request: Request, search: str = "", status: str = "", post_id: Optional[int] = None):
    website, _owner = _require_cms_owner(slug, request)
    clauses = ["c.website_id = ?"]
    params: list[object] = [website["id"]]
    if search:
        needle = f"%{search.lower()}%"
        clauses.append("(lower(c.author_name) LIKE ? OR lower(c.author_email) LIKE ? OR lower(c.content) LIKE ?)")
        params.extend([needle, needle, needle])
    if status:
        clauses.append("c.status = ?")
        params.append(status)
    if post_id:
        clauses.append("c.post_id = ?")
        params.append(post_id)
    rows = state.conn.execute(
        f"""
        SELECT c.*, p.title AS post_title
        FROM site_comments c
        LEFT JOIN site_posts p ON p.id = c.post_id AND p.website_id = c.website_id
        WHERE {" AND ".join(clauses)}
        ORDER BY c.created_at DESC
        """,
        params,
    ).fetchall()
    return {"items": [_row_dict(row) for row in rows]}


@app.put("/cms/sites/{slug}/comments/{comment_id}")
async def cms_moderate_comment(slug: str, comment_id: int, body: CommentModerationPayload, request: Request):
    website, owner = _require_cms_owner(slug, request)
    status = _validate_cms_status(body.status, {"pending", "approved", "spam", "trash"})
    state.conn.execute(
        "UPDATE site_comments SET status = ?, reply = COALESCE(?, reply), updated_at = ? WHERE id = ? AND website_id = ?",
        (status, body.reply, datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"), comment_id, website["id"]),
    )
    _record_site_activity(website["id"], owner["id"], "moderated", "comment", comment_id, f"Marked comment {status}")
    state.conn.commit()
    return {"ok": True}


@app.delete("/cms/sites/{slug}/comments/{comment_id}")
async def cms_delete_comment(slug: str, comment_id: int, request: Request):
    website, owner = _require_cms_owner(slug, request)
    state.conn.execute("DELETE FROM site_comments WHERE id = ? AND website_id = ?", (comment_id, website["id"]))
    _record_site_activity(website["id"], owner["id"], "deleted", "comment", comment_id, "Deleted comment")
    state.conn.commit()
    return {"ok": True}


@app.get("/cms/sites/{slug}/subscribers")
async def cms_subscribers(slug: str, request: Request, search: str = ""):
    website, _owner = _require_cms_owner(slug, request)
    clauses = ["website_id = ?"]
    params: list[object] = [website["id"]]
    if search:
        needle = f"%{search.lower()}%"
        clauses.append("(lower(email) LIKE ? OR lower(name) LIKE ? OR lower(source) LIKE ?)")
        params.extend([needle, needle, needle])
    rows = state.conn.execute(
        f"SELECT * FROM site_subscribers WHERE {' AND '.join(clauses)} ORDER BY created_at DESC",
        params,
    ).fetchall()
    return {"items": [_row_dict(row) for row in rows]}


@app.get("/cms/sites/{slug}/subscribers/export")
async def cms_export_subscribers(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    rows = state.conn.execute(
        "SELECT email, name, status, source, created_at FROM site_subscribers WHERE website_id = ? ORDER BY created_at DESC",
        (website["id"],),
    ).fetchall()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["email", "name", "status", "source", "created_at"])
    for row in rows:
        writer.writerow([row["email"], row["name"], row["status"], row["source"], row["created_at"]])
    return Response(
        stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{slug}-subscribers.csv"'},
    )


@app.post("/cms/sites/{slug}/subscribers", status_code=201)
async def cms_create_subscriber(slug: str, body: SubscriberPayload, request: Request):
    website, owner = _require_cms_owner(slug, request)
    clean_email = body.email.strip().lower()
    status = _validate_cms_status(body.status or "active", {"active", "unsubscribed", "bounced"})
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    cursor = state.conn.execute(
        """
        INSERT INTO site_subscribers (website_id, email, name, status, source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(website_id, email) DO UPDATE SET
            name = excluded.name,
            status = excluded.status,
            source = excluded.source,
            updated_at = excluded.updated_at
        """,
        (website["id"], clean_email, body.name or "", status, body.source or "admin", now),
    )
    row = state.conn.execute(
        "SELECT * FROM site_subscribers WHERE website_id = ? AND email = ?",
        (website["id"], clean_email),
    ).fetchone()
    _record_site_activity(website["id"], owner["id"], "created", "subscriber", row["id"] if row else None, f"Added subscriber {clean_email}")
    state.conn.commit()
    return {"item": _row_dict(row), "id": cursor.lastrowid}


@app.delete("/cms/sites/{slug}/subscribers/{subscriber_id}")
async def cms_delete_subscriber(slug: str, subscriber_id: int, request: Request):
    website, owner = _require_cms_owner(slug, request)
    state.conn.execute("DELETE FROM site_subscribers WHERE id = ? AND website_id = ?", (subscriber_id, website["id"]))
    _record_site_activity(website["id"], owner["id"], "deleted", "subscriber", subscriber_id, "Deleted subscriber")
    state.conn.commit()
    return {"ok": True}


@app.get("/cms/sites/{slug}/media")
async def cms_media(slug: str, request: Request, search: str = ""):
    website, _owner = _require_cms_owner(slug, request)
    clauses = ["website_id = ?"]
    params: list[object] = [website["id"]]
    if search:
        needle = f"%{search.lower()}%"
        clauses.append("(lower(filename) LIKE ? OR lower(original_filename) LIKE ? OR lower(alt_text) LIKE ?)")
        params.extend([needle, needle, needle])
    rows = state.conn.execute(
        f"SELECT * FROM site_media WHERE {' AND '.join(clauses)} ORDER BY created_at DESC",
        params,
    ).fetchall()
    return {"items": [_row_dict(row) for row in rows]}


@app.post("/cms/sites/{slug}/media", status_code=201)
async def cms_upload_media(
    slug: str,
    request: Request,
    file: UploadFile = File(...),
    alt_text: str = Form(default=""),
):
    website, owner = _require_cms_owner(slug, request)
    site_root = website["local_path"] or (BASE_DIR / "generated_sites" / generated_site_slug_from_url(website["base_url"]))
    path, rel_url = media_upload_path(site_root, file.filename or "upload.bin")
    content = await file.read()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    cursor = state.conn.execute(
        """
        INSERT INTO site_media
            (website_id, owner_id, filename, original_filename, content_type, size_bytes, url, alt_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (website["id"], owner["id"], path.name, file.filename or path.name, file.content_type or "", len(content), rel_url, alt_text or ""),
    )
    state.conn.commit()
    _record_site_activity(website["id"], owner["id"], "uploaded", "media", cursor.lastrowid, f"Uploaded {file.filename or path.name}")
    state.conn.commit()
    row = state.conn.execute("SELECT * FROM site_media WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"item": _row_dict(row)}


@app.delete("/cms/sites/{slug}/media/{media_id}")
async def cms_delete_media(slug: str, media_id: int, request: Request):
    website, owner = _require_cms_owner(slug, request)
    row = state.conn.execute("SELECT * FROM site_media WHERE id = ? AND website_id = ?", (media_id, website["id"])).fetchone()
    if row:
        site_root = website["local_path"] or (BASE_DIR / "generated_sites" / generated_site_slug_from_url(website["base_url"]))
        delete_file_if_local(site_root, row["url"])
    state.conn.execute("DELETE FROM site_media WHERE id = ? AND website_id = ?", (media_id, website["id"]))
    _record_site_activity(website["id"], owner["id"], "deleted", "media", media_id, "Deleted media")
    state.conn.commit()
    return {"ok": True}


@app.get("/cms/sites/{slug}/settings")
async def cms_settings(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    return {"settings": settings_dict(state.conn, website["id"])}


@app.put("/cms/sites/{slug}/settings")
async def cms_update_settings(slug: str, body: dict, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    for key, value in body.items():
        if not re.match(r"^[a-zA-Z0-9_.-]{1,80}$", str(key)):
            raise HTTPException(status_code=400, detail=f"Invalid setting key: {key}")
        state.conn.execute(
            """
            INSERT INTO site_settings (website_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(website_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (website["id"], key, json.dumps(value), now),
        )
    state.conn.commit()
    return {"settings": settings_dict(state.conn, website["id"])}


@app.get("/cms/sites/{slug}/categories")
async def cms_categories(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    settings = settings_dict(state.conn, website["id"])
    categories = settings.get("categories")
    if not categories:
        categories = [item["name"] for item in _website_categories(website)] or ["Breakfast", "Lunch", "Dinner", "Dessert"]
    return {"categories": categories}


@app.put("/cms/sites/{slug}/categories")
async def cms_update_categories(slug: str, body: dict, request: Request):
    website, owner = _require_cms_owner(slug, request)
    categories = [str(item).strip() for item in body.get("categories", []) if str(item).strip()]
    if not categories:
        raise HTTPException(status_code=400, detail="At least one category is required")
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    state.conn.execute(
        """
        INSERT INTO site_settings (website_id, key, value, updated_at)
        VALUES (?, 'categories', ?, ?)
        ON CONFLICT(website_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        (website["id"], json.dumps(categories), now),
    )
    _record_site_activity(website["id"], owner["id"], "updated", "categories", None, "Updated post categories")
    state.conn.commit()
    return {"categories": categories}


@app.get("/cms/sites/{slug}/users/profile")
async def cms_profile(slug: str, request: Request):
    _website, owner = _require_cms_owner(slug, request)
    return {"owner": public_owner(owner)}


@app.put("/cms/sites/{slug}/users/profile")
async def cms_update_profile(slug: str, body: OwnerProfilePayload, request: Request):
    website, owner = _require_cms_owner(slug, request)
    email = (body.email or owner["email"]).strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required")
    display_name = (body.display_name if body.display_name is not None else owner["display_name"]) or email
    state.conn.execute(
        "UPDATE site_owners SET email = ?, display_name = ?, updated_at = ? WHERE id = ? AND website_id = ?",
        (email, display_name, datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"), owner["id"], website["id"]),
    )
    _record_site_activity(website["id"], owner["id"], "updated", "user", owner["id"], "Updated owner profile")
    state.conn.commit()
    updated = state.conn.execute("SELECT * FROM site_owners WHERE id = ?", (owner["id"],)).fetchone()
    return {"owner": public_owner(updated)}


@app.put("/cms/sites/{slug}/users/password")
async def cms_change_password(slug: str, body: PasswordChangePayload, request: Request):
    website, owner = _require_cms_owner(slug, request)
    row = state.conn.execute("SELECT * FROM site_owners WHERE id = ? AND website_id = ?", (owner["id"], website["id"])).fetchone()
    if not row or not verify_password(body.current_password, row["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 10:
        raise HTTPException(status_code=400, detail="New password must be at least 10 characters")
    state.conn.execute(
        "UPDATE site_owners SET password_hash = ?, updated_at = ? WHERE id = ? AND website_id = ?",
        (hash_password(body.new_password), datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"), owner["id"], website["id"]),
    )
    _record_site_activity(website["id"], owner["id"], "updated", "user", owner["id"], "Changed owner password")
    state.conn.commit()
    return {"ok": True}


@app.get("/cms/sites/{slug}/domains")
async def cms_domains(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    settings = settings_dict(state.conn, website["id"])
    return {
        "base_url": website["base_url"],
        "custom_domain": settings.get("custom_domain", ""),
        "ssl_status": settings.get("ssl_status", "managed"),
        "subdomain": settings.get("subdomain", generated_site_slug_from_url(website["base_url"])),
    }


@app.put("/cms/sites/{slug}/domains")
async def cms_update_domains(slug: str, body: dict, request: Request):
    allowed = {key: body.get(key, "") for key in ("custom_domain", "ssl_status", "subdomain")}
    return await cms_update_settings(slug, allowed, request)


@app.get("/cms/sites/{slug}/appearance")
async def cms_appearance(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    settings = settings_dict(state.conn, website["id"])
    return {"appearance": {key: settings.get(key, "") for key in ("theme", "primary_color", "typography", "header_menu", "footer_content", "social_links", "logo_url", "favicon_url")}}


@app.put("/cms/sites/{slug}/appearance")
async def cms_update_appearance(slug: str, body: dict, request: Request):
    allowed = {key: body.get(key) for key in ("theme", "primary_color", "typography", "header_menu", "footer_content", "social_links", "logo_url", "favicon_url") if key in body}
    return await cms_update_settings(slug, allowed, request)


@app.get("/cms/sites/{slug}/integrations")
async def cms_integrations(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    settings = settings_dict(state.conn, website["id"])
    integrations = settings.get("integrations") or {}
    return {"integrations": integrations}


@app.put("/cms/sites/{slug}/integrations")
async def cms_update_integrations(slug: str, body: dict, request: Request):
    integrations = {
        "mailchimp": body.get("mailchimp", ""),
        "resend": body.get("resend", ""),
        "google_analytics": body.get("google_analytics", ""),
        "meta_pixel": body.get("meta_pixel", ""),
    }
    return await cms_update_settings(slug, {"integrations": integrations}, request)


@app.get("/cms/sites/{slug}/analytics")
async def cms_analytics(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    wid = website["id"]
    chart_rows = state.conn.execute(
        """
        SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS views
        FROM site_analytics_events
        WHERE website_id = ? AND event_type = 'page_view'
        GROUP BY day ORDER BY day DESC LIMIT 14
        """,
        (wid,),
    ).fetchall()
    top_posts = state.conn.execute(
        """
        SELECT p.id, p.title, p.slug, COUNT(a.id) AS views
        FROM site_posts p
        LEFT JOIN site_analytics_events a ON a.website_id = p.website_id AND a.path LIKE '%' || p.slug || '%'
        WHERE p.website_id = ?
        GROUP BY p.id
        ORDER BY views DESC, p.updated_at DESC
        LIMIT 5
        """,
        (wid,),
    ).fetchall()
    sources = state.conn.execute(
        """
        SELECT COALESCE(NULLIF(source, ''), 'direct') AS source, COUNT(*) AS visits
        FROM site_analytics_events
        WHERE website_id = ?
        GROUP BY COALESCE(NULLIF(source, ''), 'direct')
        ORDER BY visits DESC LIMIT 6
        """,
        (wid,),
    ).fetchall()
    subscriber_growth = state.conn.execute(
        "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS subscribers FROM site_subscribers WHERE website_id = ? GROUP BY day ORDER BY day DESC LIMIT 14",
        (wid,),
    ).fetchall()
    comment_activity = state.conn.execute(
        "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS comments FROM site_comments WHERE website_id = ? GROUP BY day ORDER BY day DESC LIMIT 14",
        (wid,),
    ).fetchall()
    return {
        "page_views": list(reversed([_row_dict(row) for row in chart_rows])),
        "top_posts": [_row_dict(row) for row in top_posts],
        "traffic_sources": [_row_dict(row) for row in sources],
        "subscriber_growth": list(reversed([_row_dict(row) for row in subscriber_growth])),
        "comments_activity": list(reversed([_row_dict(row) for row in comment_activity])),
    }


@app.get("/cms/sites/{slug}/backup")
async def cms_backup(slug: str, request: Request):
    website, _owner = _require_cms_owner(slug, request)
    wid = website["id"]
    payload = {
        "website": _public_website(website),
        "settings": settings_dict(state.conn, wid),
        "posts": [_row_dict(row) for row in state.conn.execute("SELECT * FROM site_posts WHERE website_id = ?", (wid,)).fetchall()],
        "pages": [_row_dict(row) for row in state.conn.execute("SELECT * FROM site_pages WHERE website_id = ?", (wid,)).fetchall()],
        "comments": [_row_dict(row) for row in state.conn.execute("SELECT * FROM site_comments WHERE website_id = ?", (wid,)).fetchall()],
        "subscribers": [_row_dict(row) for row in state.conn.execute("SELECT * FROM site_subscribers WHERE website_id = ?", (wid,)).fetchall()],
        "media": [_row_dict(row) for row in state.conn.execute("SELECT * FROM site_media WHERE website_id = ?", (wid,)).fetchall()],
        "exported_at": datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
    }
    return payload


@app.post("/cms/sites/{slug}/backup/restore")
async def cms_restore_backup(slug: str, body: dict, request: Request):
    website, owner = _require_cms_owner(slug, request)
    wid = website["id"]
    for key, value in (body.get("settings") or {}).items():
        state.conn.execute(
            """
            INSERT INTO site_settings (website_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(website_id, key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (wid, key, json.dumps(value), datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")),
        )
    _record_site_activity(wid, owner["id"], "restored", "backup", None, "Restored backup settings")
    state.conn.commit()
    return {"ok": True}


@app.post("/settings/danger/{action}")
async def danger_action(action: str):
    if action == "reset-stats":
        state.log_dashboard(None, "warn", "settings", "Stats reset requested; historical jobs retained")
        return {"ok": True, "message": "Historical job data is retained; stats are calculated live."}
    if action == "export-data":
        export_path = Path("data/dashboard-export.json")
        payload = {"stats": state.get_stats(), "settings": state.get_settings(), "prompts": state.get_prompts()}
        export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"ok": True, "path": str(export_path)}
    if action == "delete-all-jobs":
        state.conn.execute("DELETE FROM content_jobs")
        state.conn.commit()
        state.log_dashboard(None, "warn", "settings", "All jobs deleted from dashboard danger zone")
        return {"ok": True}
    raise HTTPException(status_code=404, detail="Unknown danger action")


@app.websocket("/ws/jobs")
async def websocket_jobs(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            try:
                await ws.send_json({
                    "type": "snapshot",
                    "stats": state.get_stats(),
                    "jobs": state.list_jobs(limit=20),
                    "logs": state.get_logs(limit=20),
                    "ts": time.time(),
                })
                await asyncio.wait_for(ws.receive_text(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            except Exception:
                return
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return


# ------------------------------------------------------------------
# RSS
# ------------------------------------------------------------------

@app.get("/feed")
async def feed_status():
    """Check whether the WordPress RSS feed is live."""
    return rss.verify()


# ------------------------------------------------------------------
# Dev server
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
