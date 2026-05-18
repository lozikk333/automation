"""
Content automation pipeline — Celery task chain.

Flow:  keyword
         → content_generation_task   (generate article)
         → midjourney_image_task     (generate + upscale image via ttapi.io)
         → wordpress_publish_task    (upload image + publish draft)
         → complete_task
"""

import asyncio
import json
import os
import re
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from celery import Celery, chain
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from orchestrator.state_manager import JobCancelled, StateManager, JobStatus, Stage
from content_engine.article_generator import ArticleGenerator
from content_engine.html_recipe_generator import HtmlRecipeGenerator
from compositor.featured_image_handler import FeaturedImageHandler
from publishers.wordpress import WordPressPublisher
from publishers.html_static import HtmlStaticPublisher, publish_to_local_site, publish_recipe_to_local_site
from utils.retry_logic import retry_with_backoff
from utils.google_sheets import append_to_sheet
from content_engine.recipe_card import build_tasty_shortcode, inject_into_content
from content_engine.midjourney_client import build_image_prompt, generate_midjourney_image
from services.pin_generation_service import generate_pinterest_pin
from services.pin_template_registry import DEFAULT_TEMPLATE_ID
from services.telegram_notifier import (
    format_article_failed_message,
    format_article_published_message,
    readable_ai_error,
    send_telegram_message,
)

app = Celery("content_automation")
app.config_from_object("celeryconfig")

DB_PATH = "data/state.db"
QUEUE_NAME = "automation_articles_111"
APP_TIMEZONE = ZoneInfo("Africa/Casablanca")

def _state() -> StateManager:
    return StateManager(DB_PATH)


def _website_for_job(state: StateManager, job_id: int) -> dict:
    job = state.get_job_status(job_id) or {}
    website_id = job.get("website_id")
    if website_id:
        row = state.conn.execute("SELECT * FROM websites WHERE id = ?", (website_id,)).fetchone()
        if row:
            site = dict(row)
            return {
                "id": site["id"],
                "name": site["name"],
                "base_url": site["base_url"].rstrip("/"),
                "site_type": site["site_type"] if "site_type" in site.keys() and site["site_type"] else "wordpress",
                "publish_method": site["publish_method"] if "publish_method" in site.keys() and site["publish_method"] else "wordpress_rest",
                "username": site["username"] if "username" in site.keys() else "",
                "password": site["password"] if "password" in site.keys() else "",
                "publish_endpoint": site["publish_endpoint"] if "publish_endpoint" in site.keys() else "",
                "api_enabled": bool(site["api_enabled"]) if "api_enabled" in site.keys() else False,
                "local_path": site["local_path"] if "local_path" in site.keys() else "",
                "pin_template": site["pin_template"] if "pin_template" in site.keys() and site["pin_template"] else DEFAULT_TEMPLATE_ID,
                "pin_template_style": json.loads(site["pin_template_style"]) if "pin_template_style" in site.keys() and site["pin_template_style"] else {},
                "categories": json.loads(site["categories_json"]) if "categories_json" in site.keys() and site["categories_json"] else [],
                "publish_status": site["publish_status"] if "publish_status" in site.keys() and site["publish_status"] else "draft",
            }
        print(f"[job {job_id}] Website id={website_id} not found — using .env WordPress site")

    return {
        "id": None,
        "name": "default",
        "base_url": (os.getenv("WORDPRESS_URL") or "").rstrip("/"),
        "site_type": "wordpress",
        "publish_method": "wordpress_rest",
        "username": os.getenv("WORDPRESS_USERNAME"),
        "password": os.getenv("WORDPRESS_APP_PASSWORD"),
        "publish_endpoint": "",
        "api_enabled": False,
        "local_path": "",
        "pin_template": DEFAULT_TEMPLATE_ID,
        "pin_template_style": {},
        "categories": [],
        "publish_status": "draft",
    }


def _wp_for_job(state: StateManager, job_id: int) -> tuple[WordPressPublisher, dict]:
    site = _website_for_job(state, job_id)
    print(f"[job {job_id}] WordPress target: {site['name']} ({site['base_url']})")
    return WordPressPublisher(site["base_url"], site["username"], site["password"]), site


def _publish_html_static(state: StateManager, job_id: int, site: dict, payload: dict) -> dict:
    if site.get("local_path") and Path(str(site["local_path"])).exists():
        result = publish_to_local_site(site["local_path"], payload)
    else:
        if not site.get("api_enabled"):
            raise RuntimeError("HTML static publishing API is disabled for this website")
        if not site.get("publish_endpoint") or not site.get("password"):
            raise RuntimeError("HTML static publish endpoint or API key is missing")
        result = HtmlStaticPublisher(site["publish_endpoint"], site["password"]).publish(payload)
    now = datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    if site.get("id"):
        state.conn.execute("UPDATE websites SET last_publish_at = ?, updated_at = ? WHERE id = ?", (now, now, site["id"]))
        state.conn.commit()
    return result


def _website_display_name(site: dict) -> str:
    base_url = str(site.get("base_url") or "").strip()
    host = re.sub(r"^https?://", "", base_url, flags=re.IGNORECASE).strip("/").split("/")[0]
    return host or str(site.get("name") or "WordPress")


def _job_keyword(state: StateManager, job_id: int, fallback: str = "") -> str:
    job = state.get_job_status(job_id) or {}
    return str(job.get("keyword") or fallback or "").strip()


def _notify_article_published(state: StateManager, job_id: int, site: dict, keyword: str, title: str, url: str) -> None:
    text = format_article_published_message(
        website=_website_display_name(site),
        keyword=keyword,
        title=title,
        url=url,
        published_at=datetime.now(APP_TIMEZONE),
    )
    ok = send_telegram_message(text)
    if ok:
        state.log_dashboard(job_id, "info", "telegram", "Article published notification sent")
    else:
        state.log_dashboard(job_id, "warn", "telegram", "Article published notification failed or skipped")


def _notify_article_failed(state: StateManager, job_id: int, stage: Stage, exc: Exception) -> None:
    if stage != Stage.CONTENT_GEN:
        return
    site = _website_for_job(state, job_id)
    keyword = _job_keyword(state, job_id, "")
    text = format_article_failed_message(
        website=_website_display_name(site),
        keyword=keyword,
        error=readable_ai_error(exc),
        failed_at=datetime.now(APP_TIMEZONE),
    )
    ok = send_telegram_message(text)
    if ok:
        state.log_dashboard(job_id, "info", "telegram", "Article failure notification sent")
    else:
        state.log_dashboard(job_id, "warn", "telegram", "Article failure notification failed or skipped")


def _scheduled_countdown_seconds(scheduled_time: str | None) -> int | None:
    if not scheduled_time:
        return None
    try:
        scheduled = datetime.fromisoformat(str(scheduled_time).replace("Z", "+00:00"))
    except ValueError:
        return None
    if scheduled.tzinfo is not None:
        now = datetime.now(scheduled.tzinfo)
    else:
        scheduled = scheduled.replace(tzinfo=APP_TIMEZONE)
        now = datetime.now(APP_TIMEZONE)
    return max(0, int((scheduled - now).total_seconds()))


def _delay_between_jobs_seconds(state: StateManager) -> int:
    try:
        execution = state.get_settings().get("execution", {})
        minutes = float(execution.get("delay_between_jobs_minutes", 0) or 0)
    except Exception:
        minutes = 0
    return max(0, int(minutes * 60))


def _next_pending_job(state: StateManager):
    return state.conn.execute(
        """
        SELECT id, keyword, scheduled_time
        FROM content_jobs
        WHERE status = ?
          AND (
            scheduled_time IS NOT NULL
            OR json_extract(metadata, '$.scheduler_managed') = 1
          )
        ORDER BY
          CASE WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 0 ELSE 1 END,
          scheduled_time ASC,
          id ASC
        LIMIT 1
        """,
        (JobStatus.PENDING.value,),
    ).fetchone()


def _has_active_job(state: StateManager) -> bool:
    row = state.conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM content_jobs
        WHERE status IN (?, ?)
          AND json_extract(metadata, '$.scheduler_managed') = 1
        """,
        (JobStatus.PROCESSING.value, JobStatus.RETRYING.value),
    ).fetchone()
    return bool(row and row["count"])


@app.task(bind=True)
def scheduler_tick(self):
    """
    Release exactly one ready pending job into the pipeline.
    This keeps keyword pipelines strictly sequential even when many jobs are queued.
    """
    state = _state()
    if _has_active_job(state):
        return {"status": "busy"}

    job = _next_pending_job(state)
    if not job:
        return {"status": "empty"}

    scheduled_time = job["scheduled_time"]
    countdown = _scheduled_countdown_seconds(scheduled_time)
    if countdown and countdown > 0:
        scheduler_tick.apply_async(countdown=countdown, queue=QUEUE_NAME)
        state.log_dashboard(job["id"], "info", "scheduler", f"Waiting until scheduled time: {scheduled_time}")
        return {"status": "waiting", "job_id": job["id"], "countdown": countdown}

    job_id = job["id"]
    keyword = job["keyword"]
    state.update_job(
        job_id,
        status=JobStatus.PROCESSING,
        stage=Stage.INIT,
        metadata={"scheduler_claimed_at": datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")},
    )
    result = run_pipeline(job_id, keyword)
    state.update_job(job_id, metadata={"celery_task_id": getattr(result, "id", "")})
    return {"status": "dispatched", "job_id": job_id}


def schedule_pending_jobs(countdown: int = 0):
    return scheduler_tick.apply_async(countdown=max(0, countdown), queue=QUEUE_NAME)


def _safe_food_image_prompt(keyword: str, article_title: str) -> str:
    dish = article_title or keyword or "homemade recipe"
    dish = re.sub(r"\bbanana\s+bead\b", "banana bread", dish, flags=re.IGNORECASE)
    dish = re.sub(r"\bbead\b", "bread", dish, flags=re.IGNORECASE)
    if re.search(r"\bcorn\b", dish, flags=re.IGNORECASE) and re.search(r"\bgrill|grilled|mexican\b", dish, flags=re.IGNORECASE):
        dish = "Mexican grilled corn on the cob with creamy lime topping and chili"
    dish = re.sub(r"[^a-zA-Z0-9 ,'-]", " ", dish)
    dish = re.sub(r"\s+", " ", dish).strip()[:90] or "homemade recipe"
    return (
        f"photorealistic homemade {dish}, appetizing food photography, close-up plated dish, "
        "single close-up food photo, natural kitchen light, clean real background, rich texture, warm highlights, "
        "single finished recipe, no text, no people --s 100 --v 7 --ar 10:11"
    )


def _cancelled_result(job_id: int, stage: Stage):
    state = _state()
    state.update_job(job_id, status=JobStatus.CANCELED, stage=stage, metadata={"control_state": "canceled"})
    print(f"[job {job_id}] canceled cleanly at {stage.value}")
    delay_seconds = _delay_between_jobs_seconds(state)
    if delay_seconds > 0:
        state.log_dashboard(job_id, "info", "scheduler", f"Waiting {delay_seconds // 60} minute(s) before next job")
        time.sleep(delay_seconds)
    schedule_pending_jobs()
    return {
        "job_id": job_id,
        "status": "canceled",
        "stage": stage.value,
        "cancelled": True,
        "canceled": True,
    }


def _failed_result(job_id: int, stage: Stage, exc: Exception):
    state = _state()
    state.log_error(job_id, stage.value, type(exc).__name__, str(exc))
    state.update_job(
        job_id,
        status=JobStatus.FAILED,
        stage=stage,
        metadata={
            "failure_stage": stage.value,
            "failure_type": type(exc).__name__,
            "failure_message": str(exc),
        },
    )
    print(f"[job {job_id}] failed at {stage.value}: {type(exc).__name__}: {exc}")
    try:
        _notify_article_failed(state, job_id, stage, exc)
    except Exception as telegram_exc:
        print(f"[job {job_id}] Telegram failure notification failed (non-fatal): {telegram_exc}")
        state.log_dashboard(job_id, "warn", "telegram", f"Telegram failure notification failed: {telegram_exc}")
    delay_seconds = _delay_between_jobs_seconds(state)
    if delay_seconds > 0:
        state.log_dashboard(job_id, "info", "scheduler", f"Waiting {delay_seconds // 60} minute(s) before next job")
        time.sleep(delay_seconds)
    schedule_pending_jobs()
    return {
        "job_id": job_id,
        "status": "failed",
        "stage": stage.value,
        "failed": True,
        "cancelled": True,
    }


def _retry_or_fail(task, job_id: int, stage: Stage, exc: Exception):
    state = _state()
    if stage == Stage.WP_PUBLISH and _is_wordpress_auth_error(exc):
        return _failed_result(job_id, stage, exc)
    if task.request.retries >= task.max_retries:
        return _failed_result(job_id, stage, exc)
    state.log_error(job_id, stage.value, type(exc).__name__, str(exc))
    state.update_job(job_id, status=JobStatus.RETRYING)
    raise task.retry(exc=exc)


def _is_wordpress_auth_error(exc: Exception) -> bool:
    current: BaseException | None = exc
    while current:
        response = getattr(current, "response", None)
        if response is not None and getattr(response, "status_code", None) in {401, 403}:
            return True
        current = current.__cause__ or current.__context__
    return False


def _skip_if_terminal(job_id: int, stage: Stage):
    job = _state().get_job_status(job_id)
    status = (job or {}).get("status")
    if status in {JobStatus.CANCELED.value, JobStatus.COMPLETED.value, JobStatus.FAILED.value}:
        print(f"[job {job_id}] skipping stale task at {stage.value}; status={status}")
        return {
            "job_id": job_id,
            "status": status,
            "stage": stage.value,
            "cancelled": True,
            "skipped": True,
        }
    return None


# ------------------------------------------------------------------
# Task 1 — Content generation
# ------------------------------------------------------------------

@app.task(bind=True, max_retries=0, default_retry_delay=20)
def content_generation_task(self, job_id: int, keyword: str):
    state = _state()
    try:
        stale = _skip_if_terminal(job_id, Stage.CONTENT_GEN)
        if stale:
            return stale
        state.wait_if_paused_or_cancelled(job_id)
        state.update_job(job_id, status=JobStatus.PROCESSING, stage=Stage.CONTENT_GEN)

        site = _website_for_job(state, job_id)
        site_type = str(site.get("site_type") or "wordpress")

        if site_type == "html_static":
            # HTML static recipe pipeline — produces structured JSON, not article HTML
            gen = HtmlRecipeGenerator()
            recipe = asyncio.run(gen.generate_recipe(keyword, available_categories=site.get("categories") or []))

            state.save_artifact(job_id, "article_title",     recipe["title"])
            state.save_artifact(job_id, "article_slug",      recipe["slug"])
            state.save_artifact(job_id, "article_meta_desc", recipe.get("meta_description") or "")
            state.save_artifact(job_id, "article_category",  recipe["selected_category"].get("name") or "")
            state.save_artifact(job_id, "article_selected_category", recipe["selected_category"])
            state.save_artifact(job_id, "html_recipe_data",  recipe)
            if recipe.get("heroImagePrompt"):
                state.save_artifact(job_id, "image_prompt",  recipe["heroImagePrompt"])

            print(f"[job {job_id}] HTML recipe generated: {recipe['title']}")
            print(f"[job {job_id}] Recipe category: {recipe['selected_category'].get('name') or '-'}")
            return {"job_id": job_id, "keyword": keyword, "slug": recipe["slug"]}

        # WordPress pipeline — unchanged
        gen = ArticleGenerator()
        article = asyncio.run(gen.generate_complete_article(keyword, available_categories=site.get("categories") or []))

        state.save_artifact(job_id, "article_title",     article["title"])
        state.save_artifact(job_id, "article_slug",      article["slug"])
        state.save_artifact(job_id, "article_meta_desc", article["meta_description"])
        state.save_artifact(job_id, "article_html",      article["html_content"])
        if article.get("category"):
            state.save_artifact(job_id, "article_category", article["category"])
        site_category_ids = {int(c.get("id")) for c in (site.get("categories") or []) if c.get("id")}
        if article.get("selected_category") and int(article["selected_category"].get("id", 0)) in site_category_ids:
            state.save_artifact(job_id, "article_selected_category", article["selected_category"])

        # Save recipe card data and image prompt produced in the same call —
        # downstream tasks will read these instead of making extra LLM calls.
        if article.get("recipe"):
            state.save_artifact(job_id, "recipe_json",    article["recipe"])
        if article.get("image_prompt"):
            state.save_artifact(job_id, "image_prompt",   article["image_prompt"])

        print(f"[job {job_id}] Article generated: {article['title']}")
        print(f"[job {job_id}] Article category: {article.get('category') or '-'}")
        print(f"[job {job_id}] Recipe card pre-generated: {bool(article.get('recipe'))}")
        print(f"[job {job_id}] Image prompt pre-generated: {bool(article.get('image_prompt'))}")
        return {"job_id": job_id, "keyword": keyword, "slug": article["slug"]}

    except JobCancelled:
        return _cancelled_result(job_id, Stage.CONTENT_GEN)
    except Exception as exc:
        return _retry_or_fail(self, job_id, Stage.CONTENT_GEN, exc)


# ------------------------------------------------------------------
# Task 2 — Midjourney image generation (REQUIRED)
# ------------------------------------------------------------------

@app.task(bind=True, max_retries=0, default_retry_delay=30)
def midjourney_image_task(self, prev: dict):
    if prev.get("cancelled"):
        return prev
    job_id  = prev["job_id"]
    keyword = prev["keyword"]
    state   = _state()

    try:
        stale = _skip_if_terminal(job_id, Stage.IMAGE_GEN)
        if stale:
            return stale
        state.wait_if_paused_or_cancelled(job_id)
        state.update_job(job_id, stage=Stage.IMAGE_GEN)

        article_title = state.get_artifact(job_id, "article_title") or keyword

        print("=== MIDJOURNEY STEP START ===")
        print("Keyword:", keyword)
        print("Title:", article_title)

        # Use the prompt generated alongside the article (0 extra LLM calls).
        # Fall back to build_image_prompt() only if it wasn't produced.
        cached_prompt = state.get_artifact(job_id, "image_prompt")
        if cached_prompt and isinstance(cached_prompt, str) and len(cached_prompt) > 20:
            prompt = cached_prompt
            print(f"[job {job_id}] Using pre-generated image prompt (no extra API call)")
        else:
            print(f"[job {job_id}] No cached prompt — generating image prompt via LLM")
            article_content = state.get_artifact(job_id, "article_html") or ""
            prompt = build_image_prompt(keyword, article_title, article_content)

        print("IMAGE PROMPT:", prompt)

        mj_result  = generate_midjourney_image(prompt)
        image_url  = mj_result.get("image_url")
        image_url2 = mj_result.get("image_url_2")
        image_selection = mj_result.get("image_selection")
        all_upscaled_urls = mj_result.get("all_upscaled_urls")
        image_error = mj_result.get("error")

        if not image_url:
            safe_prompt = _safe_food_image_prompt(keyword, article_title)
            state.log_dashboard(job_id, "warn", "image_generation", "Primary MidJourney prompt returned no hero image; trying one safe food prompt")
            print(f"[job {job_id}] Retrying MidJourney with safe prompt: {safe_prompt}")
            mj_result  = generate_midjourney_image(safe_prompt)
            image_url  = mj_result.get("image_url")
            image_url2 = mj_result.get("image_url_2")
            image_selection = mj_result.get("image_selection")
            all_upscaled_urls = mj_result.get("all_upscaled_urls")
            image_error = mj_result.get("error") or image_error

        if not image_url:
            detail = f": {image_error}" if image_error else ""
            raise RuntimeError(f"MidJourney did not return a usable hero image{detail}; WordPress publish stopped to avoid an article without images")

        if image_url:
            state.save_artifact(job_id, "midjourney_image_url",   image_url)
            print(f"[job {job_id}] Hero image URL: {image_url}")
        else:
            print(f"[job {job_id}] No hero image")

        if image_url2:
            state.save_artifact(job_id, "midjourney_image_url_2", image_url2)
            print(f"[job {job_id}] U2 URL: {image_url2}")
        else:
            print(f"[job {job_id}] No U2 image")

        if image_selection:
            state.save_artifact(job_id, "midjourney_image_selection", image_selection)
            state.log_dashboard(job_id, "info", "image_generation", f"Image selection: {image_selection}")
        if all_upscaled_urls:
            state.save_artifact(job_id, "midjourney_all_upscaled_urls", all_upscaled_urls)

        slug = prev.get("slug") or state.get_artifact(job_id, "article_slug") or f"job-{job_id}"
        hero_asset_path = FeaturedImageHandler.save_asset(image_url, f"assets/img/{slug}.jpg")
        pin_top_path = FeaturedImageHandler.save_asset(image_url, f"assets/pins/{slug}_pt.jpg")
        pin_bottom_path = FeaturedImageHandler.save_asset(image_url2 or image_url, f"assets/pins/{slug}_pb.jpg")
        state.save_artifact(job_id, "recipe_image_path", hero_asset_path)
        state.save_artifact(job_id, "pinterest_top_image_path", pin_top_path)
        state.save_artifact(job_id, "pinterest_bottom_image_path", pin_bottom_path)
        state.save_artifact(job_id, "pinterest_best_image_url", image_url)
        state.save_artifact(job_id, "pinterest_second_best_image_url", image_url2 or image_url)
        state.log_dashboard(job_id, "info", "image_generation", "Saved one-generation image assets for recipe, Pinterest top, and Pinterest bottom")

        # Compose the final Pinterest pin from the selected local assets only.
        pin_path = None
        try:
            site = _website_for_job(state, job_id)
            pin_template = site.get("pin_template") or DEFAULT_TEMPLATE_ID
            pin_path = generate_pinterest_pin(
                job_id           = job_id,
                article_title    = article_title,
                top_image_url    = pin_top_path,
                bottom_image_url = pin_bottom_path,
                output_path      = f"assets/pins/{slug}_pin.jpg",
                template_id      = pin_template,
                template_style   = site.get("pin_template_style") or {},
            )
            if pin_path:
                state.save_artifact(job_id, "pinterest_pin_path", pin_path)
                state.save_artifact(job_id, "pinterest_pin_template", pin_template)
                print(f"[job {job_id}] Pinterest pin created: {pin_path}")
            else:
                raise RuntimeError("Pinterest pin generation returned no file path")
        except Exception as pin_exc:
            raise RuntimeError(f"Pinterest pin generation failed; WordPress publish stopped to avoid an article without a pin image: {pin_exc}") from pin_exc

        return {
            **prev,
            "image_url": image_url,
            "image_url_2": image_url2,
            "recipe_image_path": hero_asset_path,
            "pinterest_top_image_path": pin_top_path,
            "pinterest_bottom_image_path": pin_bottom_path,
            "pin_path": pin_path,
        }

    except JobCancelled:
        return _cancelled_result(job_id, Stage.IMAGE_GEN)
    except Exception as exc:
        return _retry_or_fail(self, job_id, Stage.IMAGE_GEN, exc)


# ------------------------------------------------------------------
# Task 3 — WordPress publish
# ------------------------------------------------------------------

@app.task(bind=True, max_retries=3, default_retry_delay=15)
def wordpress_publish_task(self, prev: dict):
    if prev.get("cancelled"):
        return prev
    job_id     = prev["job_id"]
    image_url  = prev.get("image_url")
    image_url2 = prev.get("image_url_2")
    recipe_image_path = prev.get("recipe_image_path")
    pin_path   = prev.get("pin_path")
    state      = _state()

    try:
        stale = _skip_if_terminal(job_id, Stage.WP_PUBLISH)
        if stale:
            return stale
        state.wait_if_paused_or_cancelled(job_id)
        state.update_job(job_id, stage=Stage.WP_PUBLISH)

        site          = _website_for_job(state, job_id)
        slug          = state.get_artifact(job_id, "article_slug")
        article_html  = state.get_artifact(job_id, "article_html")
        article_title = state.get_artifact(job_id, "article_title") or slug
        keyword       = _job_keyword(state, job_id, slug or "")

        if str(site.get("site_type") or "wordpress") == "html_static":
            html_recipe_data = state.get_artifact(job_id, "html_recipe_data")
            if html_recipe_data and isinstance(html_recipe_data, dict):
                # New recipe pipeline — publish structured JSON as premium HTML
                html_recipe_data["featuredImage"] = image_url or html_recipe_data.get("featuredImage") or ""
                site_root = site.get("site_root") or site.get("base_url") or ""
                publish_recipe_to_local_site(site_root, html_recipe_data)
                post_url = f"{site['base_url'].rstrip('/')}/article/{html_recipe_data['slug']}/"
            else:
                # Legacy plain-HTML path — backward compatibility
                payload = {
                    "title": article_title,
                    "slug": slug,
                    "contentHtml": article_html,
                    "metaTitle": article_title,
                    "metaDescription": state.get_artifact(job_id, "article_meta_desc") or "",
                    "featuredImage": image_url or "",
                    "category": state.get_artifact(job_id, "article_category") or "",
                    "publishDate": datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
                }
                result = _publish_html_static(state, job_id, site, payload)
                post_url = result.get("url") or f"{site['base_url'].rstrip('/')}/article/{slug}/"
            if str(post_url).startswith("/"):
                post_url = f"{site['base_url'].rstrip('/')}{post_url}"
            state.save_artifact(job_id, "wp_post_url", post_url)
            state.save_artifact(job_id, "html_static_post_url", post_url)
            state.update_job(job_id, metadata={
                "wp_post_url": post_url,
                "html_static_post_url": post_url,
                "site_id": site["id"],
                "site_name": site["name"],
                "site_url": site["base_url"],
                "site_type": "html_static",
                "publish_status": "publish",
            })
            print(f"[job {job_id}] Published static HTML article: {post_url}")
            try:
                _notify_article_published(state, job_id, site, keyword, article_title, post_url)
            except Exception as telegram_exc:
                print(f"[job {job_id}] Telegram notification failed (non-fatal): {telegram_exc}")
            return {**prev, "wp_post_id": "", "wp_post_url": post_url}

        wp = WordPressPublisher(site["base_url"], site["username"], site["password"])

        # Fallback: read pin_path from state if not passed through prev
        if not pin_path:
            pin_path = state.get_artifact(job_id, "pinterest_pin_path")
        if not recipe_image_path:
            recipe_image_path = state.get_artifact(job_id, "recipe_image_path")

        if not image_url:
            raise RuntimeError("Missing hero image URL; WordPress publish stopped to avoid an article without a featured image")
        if not recipe_image_path or not os.path.exists(str(recipe_image_path)):
            raise RuntimeError("Missing saved recipe image asset; WordPress publish stopped to avoid an article without a featured image")

        if not pin_path or not os.path.exists(str(pin_path)):
            raise RuntimeError("Missing Pinterest pin image file; WordPress publish stopped to avoid an article without a pin image")

        # Upload the standard recipe image as the WordPress featured image.
        # The final Pinterest pin stays out of article content so recipe pages
        # continue to show only the normal recipe image.
        featured_media_id = 0
        wp_image_url      = None

        print(f"[job {job_id}] Uploading standard recipe image to WordPress: {recipe_image_path}")
        try:
            media             = wp.upload_media_from_file(
                file_path = recipe_image_path,
                filename  = wp.seo_filename(slug, "hero"),
                alt_text  = article_title,
                title     = article_title,
            )
            featured_media_id = media.get("id", 0)
            wp_image_url      = media.get("source_url") or image_url
            print(f"[job {job_id}] Featured media ID: {featured_media_id}")
            print(f"[job {job_id}] WordPress image URL: {wp_image_url}")
        except Exception as upload_exc:
            raise RuntimeError(f"Hero image upload failed; WordPress publish stopped to avoid an article without a featured image: {upload_exc}") from upload_exc

        if not featured_media_id or not wp_image_url:
            raise RuntimeError("Hero image upload did not return WordPress media data; WordPress publish stopped")

        # Upload the final pin for RSS/social/Pinterest distribution. Do not
        # inject it into the recipe page HTML.
        pin_wp_url = None
        pin_media_id = 0
        print(f"[job {job_id}] Uploading Pinterest pin to WordPress: {pin_path}")
        try:
            pin_filename = f"{slug}-pin.jpg"
            pin_media    = wp.upload_media_from_file(
                file_path = pin_path,
                filename  = pin_filename,
                alt_text  = article_title,
                title     = f"{article_title} - Pinterest Pin",
            )
            pin_wp_url = pin_media.get("source_url")
            pin_media_id = int(pin_media.get("id") or 0)
            state.save_artifact(job_id, "pinterest_pin_wp_url", pin_wp_url)
            state.save_artifact(job_id, "pinterest_pin_wp_media_id", pin_media_id)
            print(f"[job {job_id}] Pin uploaded to WordPress: {pin_wp_url}")
        except Exception as pin_upload_exc:
            raise RuntimeError(f"Pinterest pin upload failed; WordPress publish stopped to avoid an article without a pin image: {pin_upload_exc}") from pin_upload_exc

        if not pin_wp_url:
            raise RuntimeError("Pinterest pin upload did not return a WordPress media URL; WordPress publish stopped")
        state.save_artifact(job_id, "distribution_image_url", pin_wp_url)
        state.save_artifact(job_id, "rss_image_url", pin_wp_url)
        state.save_artifact(job_id, "social_image_url", pin_wp_url)

        # ── Recipe card ────────────────────────────────────────────────
        # Re-fetch article_html fresh from state to ensure we have latest content
        article_html = state.get_artifact(job_id, "article_html") or article_html

        print(f"[job {job_id}] ── RECIPE CARD STEP START ──")
        print(f"[job {job_id}] article_html length: {len(article_html)} chars")
        print(f"[job {job_id}] article_title: {article_title}")

        # Use the recipe JSON pre-generated alongside the article (0 extra LLM calls).
        # Do not make a second LLM call here; that extra generation was the main source
        # of long publish delays.
        cached_recipe = state.get_artifact(job_id, "recipe_json")
        if cached_recipe and isinstance(cached_recipe, dict) and cached_recipe:
            recipe = cached_recipe
            print(f"[job {job_id}] Using pre-generated recipe JSON (no extra API call) ✅")
            print(f"[job {job_id}] Recipe keys: {list(recipe.keys())}")
        else:
            recipe = None
            print(f"[job {job_id}] No cached recipe_json — skipping recipe card generation")

        if recipe:
            # Step 2: Build shortcode (creates tasty_recipe WP post internally)
            print(f"[job {job_id}] Calling build_tasty_shortcode...")
            shortcode = build_tasty_shortcode(
                recipe    = recipe,
                title     = article_title,
                wp_url    = site["base_url"],
                username  = site["username"],
                password  = site["password"],
                image_url = wp_image_url or "",
                media_id  = featured_media_id,
            )
            print(f"[job {job_id}] build_tasty_shortcode result: {shortcode or 'None — FAILED'}")

            if shortcode:
                # Step 3: Inject shortcode into article before FAQ
                article_html = inject_into_content(shortcode, article_html)
                state.save_artifact(job_id, "article_html", article_html)
                state.save_artifact(job_id, "tasty_recipe_shortcode", shortcode)
                print(f"[job {job_id}] Recipe card injected into article ✅")
                print(f"[job {job_id}] Updated article_html length: {len(article_html)} chars")
            else:
                print(f"[job {job_id}] ❌ Shortcode build failed — publishing without recipe card")
        else:
            print(f"[job {job_id}] ❌ Recipe JSON generation failed — publishing without recipe card")

        print(f"[job {job_id}] ── RECIPE CARD STEP END ──")

        # Category
        categories = site.get("categories") or wp.fetch_categories()
        recipe_category = ""
        if cached_recipe and isinstance(cached_recipe, dict):
            details = cached_recipe.get("Details") or {}
            if isinstance(details, dict):
                recipe_category = details.get("Category", "")
        if not recipe_category:
            recipe_category = state.get_artifact(job_id, "article_category") or ""
        selected_category = state.get_artifact(job_id, "article_selected_category")
        cat_id = None
        if isinstance(selected_category, dict) and selected_category.get("id"):
            selected_id = int(selected_category["id"])
            known_ids = {int(c.get("id")) for c in categories if c.get("id")}
            if not known_ids or selected_id in known_ids:
                cat_id = selected_id
                state.log_dashboard(job_id, "info", "wordpress", f"Using AI selected category: {selected_category.get('name')} (id={cat_id})")
        if not cat_id:
            cat_id = wp.select_best_category(
                keyword,
                categories,
                title=article_title,
                recipe_category=recipe_category,
            )

        publish_status = str(site.get("publish_status") or "draft").strip().lower()
        if publish_status not in {"draft", "publish"}:
            publish_status = "draft"

        # Create WordPress post as draft or publish, based on website setting.
        post = wp.create_post(
            title=article_title,
            content=article_html,
            slug=slug,
            meta_description=state.get_artifact(job_id, "article_meta_desc"),
            featured_image_id=featured_media_id,
            category_ids=[cat_id],
            status=publish_status,
            social_image_url=pin_wp_url,
            social_image_id=pin_media_id,
            pin_image_url=pin_wp_url,
        )

        state.save_artifact(job_id, "wp_post_id",  str(post["id"]))
        state.save_artifact(job_id, "wp_post_url", post["link"])
        state.update_job(job_id, metadata={
            "wp_post_id":  post["id"],
            "wp_post_url": post["link"],
            "wp_site_id": site["id"],
            "wp_site_name": site["name"],
            "wp_site_url": site["base_url"],
            "wp_publish_status": publish_status,
        })

        print(f"[job {job_id}] Published: {post['link']}")

        try:
            _notify_article_published(state, job_id, site, keyword, article_title, post["link"])
        except Exception as telegram_exc:
            print(f"[job {job_id}] Telegram notification failed (non-fatal): {telegram_exc}")
            state.log_dashboard(job_id, "warn", "telegram", f"Telegram notification failed: {telegram_exc}")

        # Append row to Google Sheet (non-fatal — never blocks pipeline)
        print(f"[job {job_id}] Sheet U1: {image_url}")
        print(f"[job {job_id}] Sheet U2: {image_url2}")
        try:
            append_to_sheet({
                "keyword":     state.get_artifact(job_id, "article_slug") or keyword,
                "title":       article_title,
                "description": state.get_artifact(job_id, "article_meta_desc") or "",
                "image_u1":    image_url  or "",
                "image_u2":    image_url2 or "",
                "recipe_image": wp_image_url or "",
                "pinterest_pin": pin_wp_url or "",
                "rss_image": pin_wp_url or "",
                "social_image": pin_wp_url or "",
                "url":         post["link"],
            })
        except Exception as sheet_exc:
            print(f"[job {job_id}] Google Sheets failed (non-fatal): {sheet_exc}")

        return {**prev, "wp_post_id": post["id"], "wp_post_url": post["link"]}

    except JobCancelled:
        return _cancelled_result(job_id, Stage.WP_PUBLISH)
    except Exception as exc:
        return _retry_or_fail(self, job_id, Stage.WP_PUBLISH, exc)


# ------------------------------------------------------------------
# Task 4 — Complete
# ------------------------------------------------------------------

@app.task(bind=True)
def complete_task(self, prev: dict):
    if prev.get("cancelled"):
        return prev
    job_id = prev["job_id"]
    state  = _state()
    stale = _skip_if_terminal(job_id, Stage.COMPLETE)
    if stale:
        return stale
    try:
        state.wait_if_paused_or_cancelled(job_id)
    except JobCancelled:
        return _cancelled_result(job_id, Stage.COMPLETE)
    state.update_job(job_id, status=JobStatus.COMPLETED, stage=Stage.COMPLETE)
    print(f"[job {job_id}] Pipeline complete ✅  {prev.get('wp_post_url', '')}")
    delay_seconds = _delay_between_jobs_seconds(state)
    if delay_seconds > 0:
        state.log_dashboard(job_id, "info", "scheduler", f"Waiting {delay_seconds // 60} minute(s) before next job")
        time.sleep(delay_seconds)
    schedule_pending_jobs()
    return {**prev, "status": "complete"}


# ------------------------------------------------------------------
# Entry point — called from the API server
# ------------------------------------------------------------------

def run_pipeline(job_id: int, keyword: str):
    pipeline = chain(
        content_generation_task.s(job_id, keyword).set(queue=QUEUE_NAME),
        midjourney_image_task.s().set(queue=QUEUE_NAME),
        wordpress_publish_task.s().set(queue=QUEUE_NAME),
        complete_task.s().set(queue=QUEUE_NAME),
    )
    result = pipeline.apply_async(queue=QUEUE_NAME)
    state = _state()
    state.update_job(job_id, metadata={"celery_root_id": getattr(result, "id", None)})
    return result
