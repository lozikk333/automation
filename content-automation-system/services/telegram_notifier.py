from __future__ import annotations

import html
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
import requests
from dotenv import load_dotenv


load_dotenv()
APP_TIMEZONE = ZoneInfo("Africa/Casablanca")


def _telegram_config() -> tuple[str, str]:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
    return token, chat_id


def send_telegram_message(text: str, chat_id: str | None = None) -> bool:
    token, default_chat_id = _telegram_config()
    target_chat_id = (chat_id or default_chat_id or "").strip()
    if not token or not target_chat_id:
        print("[telegram] skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing")
        return False

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": target_chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            },
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            print(f"[telegram] send failed: {payload}")
            return False
        return True
    except Exception as exc:
        print(f"[telegram] send failed: {type(exc).__name__}: {exc}")
        return False


def readable_ai_error(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    cause = exc.__cause__

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
    elif isinstance(cause, httpx.HTTPStatusError):
        status_code = cause.response.status_code
    else:
        status_code = None

    if status_code in {401, 403} or "401" in lowered or "unauthorized" in lowered or "invalid api key" in lowered:
        return "API key invalid"
    if status_code in {402, 429} or "402" in lowered or "payment required" in lowered or "429" in lowered or "quota" in lowered or "rate limit" in lowered:
        return "API quota exceeded"
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)) or isinstance(cause, (httpx.TimeoutException, TimeoutError)):
        return "AI timeout"
    if "timeout" in lowered or "readtimeout" in lowered or "no response" in lowered or "network failure" in lowered:
        return "AI timeout"
    if "empty content" in lowered or "empty response" in lowered or "returned empty" in lowered or "no choices" in lowered:
        return "Empty response"
    if "failed to parse json" in lowered or "invalid json" in lowered:
        return "Invalid AI response"
    if "article generation failed" in lowered or "quality checks" in lowered or "failed article contract" in lowered:
        return "Generation failed"
    return message[:240] or "Generation failed"


def format_article_published_message(
    *,
    website: str,
    keyword: str,
    title: str,
    url: str,
    published_at: datetime | None = None,
) -> str:
    stamp = (published_at or datetime.now(APP_TIMEZONE)).strftime("%Y-%m-%d %H:%M")
    return (
        "✅ <b>Article Published</b>\n\n"
        f"🌐 <b>Website:</b> {html.escape(website)}\n"
        f"🔑 <b>Keyword:</b> {html.escape(keyword)}\n"
        f"📝 <b>Title:</b> {html.escape(title)}\n"
        f"🔗 <b>Link:</b> {html.escape(url)}\n"
        "📌 <b>Status:</b> DONE\n"
        f"⏱ <b>Time:</b> {stamp}"
    )


def format_article_failed_message(
    *,
    website: str,
    keyword: str,
    error: str,
    failed_at: datetime | None = None,
) -> str:
    stamp = (failed_at or datetime.now(APP_TIMEZONE)).strftime("%Y-%m-%d %H:%M")
    return (
        "❌ <b>Article Failed</b>\n\n"
        f"🌐 <b>Website:</b> {html.escape(website)}\n"
        f"🔑 <b>Keyword:</b> {html.escape(keyword)}\n"
        f"⚠️ <b>Error:</b> {html.escape(error)}\n"
        f"⏱ <b>Time:</b> {stamp}"
    )
