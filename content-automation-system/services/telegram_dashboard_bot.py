from __future__ import annotations

import html
import os
import sqlite3
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from services.telegram_notifier import _telegram_config, send_telegram_message


load_dotenv()

APP_TIMEZONE = ZoneInfo("Africa/Casablanca")
DB_PATH = os.getenv("DB_PATH", "data/state.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _today_bounds() -> tuple[str, str]:
    now = datetime.now(APP_TIMEZONE)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.replace(tzinfo=None).isoformat(sep=" "), end.replace(tzinfo=None).isoformat(sep=" ")


def _artifact(conn: sqlite3.Connection, job_id: int, artifact_type: str) -> str:
    row = conn.execute(
        """
        SELECT artifact_data
        FROM content_artifacts
        WHERE job_id = ? AND artifact_type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (job_id, artifact_type),
    ).fetchone()
    return str(row["artifact_data"]) if row else ""


def _last_error(conn: sqlite3.Connection, job_id: int) -> str:
    row = conn.execute(
        """
        SELECT error_message
        FROM error_log
        WHERE job_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (job_id,),
    ).fetchone()
    return str(row["error_message"]) if row else ""


def _short(text: str, limit: int = 70) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def handle_telegram_command(message_text: str) -> str | None:
    command = (message_text or "").strip().split()[0].lower()
    if "@" in command:
        command = command.split("@", 1)[0]

    if command == "/start":
        return "Bot is active and connected to the article pipeline."
    if command == "/stats":
        return _stats_today()
    if command == "/jobs":
        return _last_jobs()
    if command == "/errors":
        return _recent_errors()
    if command == "/last":
        return _last_published()
    return None


def _stats_today() -> str:
    start, end = _today_bounds()
    with _connect() as conn:
        published = conn.execute(
            "SELECT COUNT(*) AS count FROM content_jobs WHERE status = 'completed' AND COALESCE(finished_at, updated_at, created_at) >= ? AND COALESCE(finished_at, updated_at, created_at) < ?",
            (start, end),
        ).fetchone()["count"]
        failed = conn.execute(
            "SELECT COUNT(*) AS count FROM content_jobs WHERE status = 'failed' AND COALESCE(finished_at, updated_at, created_at) >= ? AND COALESCE(finished_at, updated_at, created_at) < ?",
            (start, end),
        ).fetchone()["count"]
        last = conn.execute(
            """
            SELECT id, keyword
            FROM content_jobs
            WHERE status = 'completed'
            ORDER BY COALESCE(finished_at, updated_at, created_at) DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        last_title = _artifact(conn, last["id"], "article_title") if last else "-"

    total = published + failed
    success_rate = round((published / total) * 100) if total else 0
    return (
        "📊 <b>Stats Today</b>\n\n"
        f"✅ <b>Published:</b> {published}\n"
        f"❌ <b>Failed:</b> {failed}\n"
        f"📈 <b>Success Rate:</b> {success_rate}%\n"
        f"📝 <b>Last Article:</b> {html.escape(_short(last_title, 80))}"
    )


def _last_jobs() -> str:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, keyword, status
            FROM content_jobs
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        if not rows:
            return "🧾 <b>Last Jobs</b>\n\nNo jobs yet."

        lines = ["🧾 <b>Last Jobs</b>", ""]
        for index, row in enumerate(rows, start=1):
            status = row["status"]
            icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
            error = ""
            if status == "failed":
                error_text = _short(_last_error(conn, row["id"]), 34)
                error = f" ({html.escape(error_text)})" if error_text else ""
            lines.append(f"{index}. {icon} {html.escape(_short(row['keyword'], 45))}{error}")
        return "\n".join(lines)


def _recent_errors() -> str:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT error_message
            FROM error_log
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

    if not rows:
        return "⚠️ <b>Recent Errors</b>\n\nNo recent errors."
    lines = ["⚠️ <b>Recent Errors</b>", ""]
    lines.extend(f"- {html.escape(_short(row['error_message'], 90))}" for row in rows)
    return "\n".join(lines)


def _last_published() -> str:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, keyword
            FROM content_jobs
            WHERE status = 'completed'
            ORDER BY COALESCE(finished_at, updated_at, created_at) DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return "📝 <b>Last Article</b>\n\nNo published articles yet."
        title = _artifact(conn, row["id"], "article_title") or row["keyword"]
        link = _artifact(conn, row["id"], "wp_post_url") or "-"

    return (
        "📝 <b>Last Article</b>\n\n"
        f"<b>Title:</b> {html.escape(_short(title, 90))}\n"
        f"<b>Keyword:</b> {html.escape(_short(row['keyword'], 90))}\n"
        f"<b>Link:</b> {html.escape(link)}"
    )


def poll_telegram_commands(interval_seconds: int = 4) -> None:
    token, allowed_chat_id = _telegram_config()
    if not token:
        print("[telegram-bot] TELEGRAM_BOT_TOKEN is missing")
        return

    offset = 0
    print("[telegram-bot] command polling started")
    while True:
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": offset, "timeout": 25, "allowed_updates": ["message"]},
                timeout=35,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                print(f"[telegram-bot] getUpdates failed: {payload}")
                time.sleep(interval_seconds)
                continue

            for update in payload.get("result", []):
                offset = max(offset, int(update.get("update_id", 0)) + 1)
                message = update.get("message") or {}
                chat = message.get("chat") or {}
                chat_id = str(chat.get("id", ""))
                text = str(message.get("text") or "").strip()
                if allowed_chat_id and chat_id != allowed_chat_id:
                    continue
                if not text.startswith("/"):
                    continue
                reply = handle_telegram_command(text)
                if reply:
                    send_telegram_message(reply, chat_id=chat_id)
        except Exception as exc:
            print(f"[telegram-bot] polling error: {type(exc).__name__}: {exc}")
            time.sleep(interval_seconds)
