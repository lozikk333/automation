import sqlite3
import json
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("Africa/Casablanca")


def app_now_iso() -> str:
    return datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELED = "canceled"


class Stage(Enum):
    INIT = "init"
    RESEARCH = "research"
    CONTENT_GEN = "content_generation"
    IMAGE_GEN = "image_generation"
    IMAGE_COMP = "image_composition"
    WP_PUBLISH = "wordpress_publish"
    PIN_META = "pinterest_metadata"
    PIN_SCHEDULE = "pinterest_schedule"
    COMPLETE = "complete"


class JobCancelled(Exception):
    """Raised when a dashboard cancel request reaches a safe checkpoint."""


class StateManager:
    def __init__(self, db_path="data/state.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _init_db(self):
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
        with open(schema_path, "r") as f:
            self.conn.executescript(f.read())
        self._ensure_columns()
        self._seed_dashboard_defaults()
        self.conn.commit()

    def _ensure_columns(self):
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(content_jobs)").fetchall()}
        if "website_id" not in columns:
            self.conn.execute("ALTER TABLE content_jobs ADD COLUMN website_id INTEGER")
        if "batch_name" not in columns:
            self.conn.execute("ALTER TABLE content_jobs ADD COLUMN batch_name TEXT")
        if "celery_task_id" not in columns:
            self.conn.execute("ALTER TABLE content_jobs ADD COLUMN celery_task_id TEXT")
        if "scheduled_time" not in columns:
            self.conn.execute("ALTER TABLE content_jobs ADD COLUMN scheduled_time TIMESTAMP")
        if "started_at" not in columns:
            self.conn.execute("ALTER TABLE content_jobs ADD COLUMN started_at TIMESTAMP")
        if "finished_at" not in columns:
            self.conn.execute("ALTER TABLE content_jobs ADD COLUMN finished_at TIMESTAMP")
        website_columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(websites)").fetchall()}
        website_defaults = {
            "site_type": "TEXT NOT NULL DEFAULT 'wordpress'",
            "publish_method": "TEXT NOT NULL DEFAULT 'wordpress_rest'",
            "status": "TEXT NOT NULL DEFAULT 'active'",
            "publish_endpoint": "TEXT",
            "api_key_hash": "TEXT",
            "api_enabled": "INTEGER NOT NULL DEFAULT 0",
            "last_publish_at": "TIMESTAMP",
            "local_path": "TEXT",
            "updated_at": "TIMESTAMP",
        }
        for column, definition in website_defaults.items():
            if column not in website_columns:
                self.conn.execute(f"ALTER TABLE websites ADD COLUMN {column} {definition}")
        website_columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(websites)").fetchall()}
        if "pin_template" not in website_columns:
            self.conn.execute("ALTER TABLE websites ADD COLUMN pin_template TEXT NOT NULL DEFAULT 'u1_u2_white_band'")
        if "pin_template_style" not in website_columns:
            self.conn.execute("ALTER TABLE websites ADD COLUMN pin_template_style TEXT")
        if "categories_json" not in website_columns:
            self.conn.execute("ALTER TABLE websites ADD COLUMN categories_json TEXT")
        if "categories_synced_at" not in website_columns:
            self.conn.execute("ALTER TABLE websites ADD COLUMN categories_synced_at TIMESTAMP")
        if "publish_status" not in website_columns:
            self.conn.execute("ALTER TABLE websites ADD COLUMN publish_status TEXT NOT NULL DEFAULT 'draft'")
        self._ensure_cms_columns()
        self._ensure_canceled_status()

    def _ensure_cms_columns(self):
        def columns(table: str) -> set[str]:
            return {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()}

        post_columns = columns("site_posts")
        post_defaults = {
            "category": "TEXT",
            "tags": "TEXT DEFAULT '[]'",
            "seo_title": "TEXT",
            "meta_description": "TEXT",
        }
        for column, definition in post_defaults.items():
            if column not in post_columns:
                self.conn.execute(f"ALTER TABLE site_posts ADD COLUMN {column} {definition}")

        comment_columns = columns("site_comments")
        if "reply" not in comment_columns:
            self.conn.execute("ALTER TABLE site_comments ADD COLUMN reply TEXT")

    def _ensure_canceled_status(self):
        row = self.conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'content_jobs'"
        ).fetchone()
        if not row or "'canceled'" in (row["sql"] or ""):
            return

        self.conn.commit()
        self.conn.execute("PRAGMA foreign_keys = OFF")
        try:
            self.conn.executescript(
                """
                CREATE TABLE content_jobs_new (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword        TEXT NOT NULL,
                    status         TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'completed', 'failed', 'retrying', 'canceled')),
                    stage          TEXT CHECK(stage IN (
                                      'init', 'research', 'content_generation', 'image_generation',
                                      'image_composition', 'wordpress_publish', 'pinterest_metadata',
                                      'pinterest_schedule', 'complete'
                                  )),
                    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scheduled_time TIMESTAMP,
                    started_at     TIMESTAMP,
                    finished_at    TIMESTAMP,
                    metadata       JSON DEFAULT '{}',
                    website_id     INTEGER,
                    batch_name     TEXT,
                    celery_task_id TEXT
                );

                INSERT INTO content_jobs_new
                    (id, keyword, status, stage, created_at, updated_at, scheduled_time, started_at, finished_at, metadata, website_id, batch_name, celery_task_id)
                SELECT id, keyword, status, stage, created_at, updated_at, scheduled_time, started_at, finished_at, metadata, website_id, batch_name, celery_task_id
                FROM content_jobs;

                DROP TABLE content_jobs;
                ALTER TABLE content_jobs_new RENAME TO content_jobs;
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON content_jobs(status);
                CREATE INDEX IF NOT EXISTS idx_jobs_keyword ON content_jobs(keyword);
                """
            )
            self.conn.commit()
        finally:
            self.conn.execute("PRAGMA foreign_keys = ON")

    def _seed_dashboard_defaults(self):
        prompts = [
            (
                "article",
                "Article Prompt",
                "Primary article generation prompt.",
                ["keyword", "website_name"],
                "Create a helpful SEO recipe article for {keyword}. Include a clear title, meta description, sections, FAQ, and recipe details.",
            ),
            (
                "hero_image",
                "Hero Image Prompt",
                "Food photography prompt used for hero images.",
                ["keyword", "article_title"],
                "Amateur iPhone food photo of {keyword}, close-up, natural kitchen light, simple background, mouthwatering texture --ar 10:11",
            ),
            (
                "recipe",
                "Recipe Prompt",
                "Recipe JSON extraction prompt.",
                ["article_content"],
                "Extract a valid recipe JSON object from this article content: {article_content}",
            ),
            (
                "pinterest_pin",
                "Pinterest Pin Prompt",
                "Prompt guidance for Pinterest pin copy and visuals.",
                ["keyword", "article_title"],
                "Create concise Pinterest metadata and a compelling pin title for {article_title}.",
            ),
        ]
        for prompt_id, name, desc, variables, content in prompts:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO dashboard_prompts
                    (id, name, description, variables, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (prompt_id, name, desc, json.dumps(variables), content),
            )

        settings = {
            "execution": {
                "worker_concurrency": 1,
                "job_timeout_minutes": 45,
                "max_retries": 3,
                "polling_interval_seconds": 5,
                "delay_between_jobs_minutes": 0,
            },
            "storage": {
                "cleanup_enabled": False,
                "archive_after_days": 30,
                "keep_logs_days": 14,
            },
            "notifications": {
                "email_enabled": False,
                "slack_enabled": False,
                "notify_on_failure": True,
            },
            "security": {
                "api_auth_enabled": False,
                "two_factor_enabled": False,
            },
        }
        for key, value in settings.items():
            existing = self.conn.execute("SELECT value FROM dashboard_settings WHERE key = ?", (key,)).fetchone()
            if existing:
                try:
                    existing_value = json.loads(existing["value"])
                except json.JSONDecodeError:
                    existing_value = {}
                if isinstance(existing_value, dict) and isinstance(value, dict):
                    merged = {**value, **existing_value}
                    if merged != existing_value:
                        self.conn.execute(
                            "UPDATE dashboard_settings SET value = ?, updated_at = ? WHERE key = ?",
                            (json.dumps(merged), app_now_iso(), key),
                        )
                continue
            self.conn.execute(
                "INSERT OR IGNORE INTO dashboard_settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )

    def create_job(
        self,
        keyword: str,
        website_id: int | None = None,
        batch_name: str | None = None,
        scheduled_time: str | None = None,
    ) -> int:
        cursor = self.conn.cursor()
        now = app_now_iso()
        metadata = {"scheduler_managed": True}
        cursor.execute(
            """
            INSERT INTO content_jobs (keyword, status, stage, created_at, updated_at, metadata, website_id, batch_name, scheduled_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (keyword, JobStatus.PENDING.value, Stage.INIT.value, now, now, json.dumps(metadata), website_id, batch_name, scheduled_time)
        )
        self.conn.commit()
        schedule_note = f" scheduled for {scheduled_time}" if scheduled_time else ""
        self.log_dashboard(cursor.lastrowid, "info", "api", f"Job created for keyword: {keyword}{schedule_note}")
        return cursor.lastrowid

    def update_job(self, job_id: int, status=None, stage=None, metadata: dict = None):
        updates = []
        params = []

        if status is not None:
            status_value = status.value if isinstance(status, JobStatus) else status
            updates.append("status = ?")
            params.append(status_value)
            if status_value == JobStatus.PROCESSING.value:
                row = self.conn.execute("SELECT started_at FROM content_jobs WHERE id = ?", (job_id,)).fetchone()
                if row and not row["started_at"]:
                    updates.append("started_at = ?")
                    params.append(app_now_iso())
            if status_value in {JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELED.value}:
                updates.append("finished_at = ?")
                params.append(app_now_iso())
        if stage is not None:
            updates.append("stage = ?")
            params.append(stage.value if isinstance(stage, Stage) else stage)
        if metadata is not None:
            existing = self.get_job_metadata(job_id)
            existing.update(metadata)
            updates.append("metadata = ?")
            params.append(json.dumps(existing))

        updates.append("updated_at = ?")
        params.append(app_now_iso())
        params.append(job_id)

        self.conn.execute(
            f"UPDATE content_jobs SET {', '.join(updates)} WHERE id = ?",
            params
        )
        self.conn.commit()
        pieces = []
        if status is not None:
            pieces.append(f"status={status.value if isinstance(status, JobStatus) else status}")
        if stage is not None:
            pieces.append(f"stage={stage.value if isinstance(stage, Stage) else stage}")
        if pieces:
            self.log_dashboard(job_id, "info", "pipeline", "Job updated: " + ", ".join(pieces))

    def save_artifact(self, job_id: int, artifact_type: str, artifact_data):
        data_str = (
            json.dumps(artifact_data)
            if isinstance(artifact_data, (dict, list))
            else str(artifact_data)
        )
        self.conn.execute(
            "INSERT INTO content_artifacts (job_id, artifact_type, artifact_data) VALUES (?, ?, ?)",
            (job_id, artifact_type, data_str)
        )
        self.conn.commit()
        self.log_dashboard(job_id, "debug", "artifact", f"Saved artifact: {artifact_type}")

    def get_artifact(self, job_id: int, artifact_type: str):
        cursor = self.conn.execute(
            "SELECT artifact_data FROM content_artifacts WHERE job_id = ? AND artifact_type = ? ORDER BY id DESC LIMIT 1",
            (job_id, artifact_type)
        )
        row = cursor.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return row[0]

    def get_job_metadata(self, job_id: int) -> dict:
        cursor = self.conn.execute(
            "SELECT metadata FROM content_jobs WHERE id = ?", (job_id,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else {}

    def get_job_status(self, job_id: int) -> dict | None:
        cursor = self.conn.execute(
            """
            SELECT id, keyword, status, stage, created_at, updated_at, metadata,
                   website_id, batch_name, scheduled_time, started_at, finished_at
            FROM content_jobs WHERE id = ?
            """,
            (job_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "keyword": row["keyword"],
            "status": row["status"],
            "stage": row["stage"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"]),
            "website_id": row["website_id"],
            "batch_name": row["batch_name"],
            "scheduled_time": row["scheduled_time"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }

    def list_jobs(self, status: str = None, limit: int = 50) -> list:
        if status:
            cursor = self.conn.execute(
                """
                SELECT id, keyword, status, stage, updated_at, created_at, website_id, batch_name,
                       scheduled_time, started_at, finished_at
                FROM content_jobs WHERE status = ? ORDER BY id DESC LIMIT ?
                """,
                (status, limit)
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT id, keyword, status, stage, updated_at, created_at, website_id, batch_name,
                       scheduled_time, started_at, finished_at
                FROM content_jobs ORDER BY id DESC LIMIT ?
                """,
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]

    def log_error(self, job_id: int, stage: str, error_type: str, error_message: str, retry_count: int = 0):
        self.conn.execute(
            "INSERT INTO error_log (job_id, stage, error_type, error_message, retry_count) VALUES (?, ?, ?, ?, ?)",
            (job_id, stage, error_type, error_message, retry_count)
        )
        self.conn.commit()
        self.log_dashboard(job_id, "error", stage or "pipeline", f"{error_type}: {error_message}")

    def log_dashboard(self, job_id: int | None, level: str, service: str, message: str):
        self.conn.execute(
            "INSERT INTO dashboard_logs (job_id, level, service, message) VALUES (?, ?, ?, ?)",
            (job_id, level, service, message),
        )
        self.conn.commit()

    def get_logs(self, job_id: int | None = None, level: str | None = None, limit: int = 200) -> list:
        where = []
        params = []
        if job_id is not None:
            where.append("job_id = ?")
            params.append(job_id)
        if level:
            where.append("level = ?")
            params.append(level)
        sql = "SELECT id, job_id, level, service, message, created_at FROM dashboard_logs"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return [dict(row) for row in self.conn.execute(sql, params).fetchall()]

    def get_job_detail(self, job_id: int) -> dict | None:
        job = self.get_job_status(job_id)
        if not job:
            return None
        artifacts = {}
        rows = self.conn.execute(
            "SELECT artifact_type, artifact_data FROM content_artifacts WHERE job_id = ? ORDER BY id",
            (job_id,),
        ).fetchall()
        for row in rows:
            try:
                artifacts[row["artifact_type"]] = json.loads(row["artifact_data"])
            except (json.JSONDecodeError, TypeError):
                artifacts[row["artifact_type"]] = row["artifact_data"]
        errors = [dict(row) for row in self.conn.execute(
            """
            SELECT id, stage, error_type, error_message, retry_count, created_at
            FROM error_log WHERE job_id = ? ORDER BY id DESC LIMIT 20
            """,
            (job_id,),
        ).fetchall()]
        control = self.get_job_control(job_id)
        return {
            **job,
            "artifacts": artifacts,
            "errors": errors,
            "control": control,
            "progress": self.progress_for_stage(job["stage"], job["status"]),
        }

    def get_stats(self) -> dict:
        counts = {row["status"]: row["count"] for row in self.conn.execute(
            "SELECT status, COUNT(*) AS count FROM content_jobs GROUP BY status"
        ).fetchall()}
        total = sum(counts.values())
        completed = counts.get(JobStatus.COMPLETED.value, 0)
        failed = counts.get(JobStatus.FAILED.value, 0)
        canceled = counts.get(JobStatus.CANCELED.value, 0)
        processing = counts.get(JobStatus.PROCESSING.value, 0) + counts.get(JobStatus.PENDING.value, 0) + counts.get(JobStatus.RETRYING.value, 0)
        success_rate = round((completed / total) * 100, 1) if total else 0
        activity = [dict(row) for row in self.conn.execute(
            """
            SELECT date(created_at) AS day,
                   COUNT(*) AS total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                   SUM(CASE WHEN status = 'canceled' THEN 1 ELSE 0 END) AS canceled
            FROM content_jobs
            WHERE date(created_at) >= date('now', '-6 day')
            GROUP BY date(created_at)
            ORDER BY date(created_at)
            """
        ).fetchall()]
        avg_row = self.conn.execute(
            """
            SELECT AVG((julianday(updated_at) - julianday(created_at)) * 86400.0) AS seconds
            FROM content_jobs
            WHERE status = 'completed'
            """
        ).fetchone()
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "canceled": canceled,
            "processing": processing,
            "success_rate": success_rate,
            "avg_duration_seconds": round(avg_row["seconds"] or 0),
            "activity": activity,
        }

    def progress_for_stage(self, stage: str | None, status: str | None) -> int:
        if status == JobStatus.COMPLETED.value:
            return 100
        if status == JobStatus.FAILED.value:
            return 0
        if status == JobStatus.CANCELED.value:
            return 0
        values = {
            Stage.INIT.value: 5,
            Stage.RESEARCH.value: 15,
            Stage.CONTENT_GEN.value: 30,
            Stage.IMAGE_GEN.value: 55,
            Stage.IMAGE_COMP.value: 68,
            Stage.WP_PUBLISH.value: 82,
            Stage.PIN_META.value: 93,
            Stage.PIN_SCHEDULE.value: 96,
            Stage.COMPLETE.value: 100,
        }
        return values.get(stage or "", 0)

    def set_job_control(self, job_id: int, action: str, reason: str | None = None):
        self.conn.execute(
            """
            INSERT INTO job_control (job_id, action, reason, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                action = excluded.action,
                reason = excluded.reason,
                updated_at = excluded.updated_at
            """,
            (job_id, action, reason, app_now_iso()),
        )
        self.conn.commit()
        self.log_dashboard(job_id, "warn" if action in {"paused", "cancel_requested"} else "info", "control", f"Control action: {action}")

    def get_job_control(self, job_id: int) -> dict:
        row = self.conn.execute(
            "SELECT job_id, action, reason, updated_at FROM job_control WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if not row:
            return {"job_id": job_id, "action": "active", "reason": None, "updated_at": None}
        return dict(row)

    def wait_if_paused_or_cancelled(self, job_id: int):
        while True:
            control = self.get_job_control(job_id)
            if control["action"] == "cancel_requested":
                self.update_job(job_id, status=JobStatus.CANCELED, metadata={"control_state": "canceled"})
                raise JobCancelled("Job cancelled from dashboard")
            if control["action"] != "paused":
                return
            self.log_dashboard(job_id, "warn", "control", "Job paused; waiting for resume")
            time.sleep(5)

    def get_prompts(self) -> list:
        rows = self.conn.execute(
            "SELECT id, name, description, variables, content, updated_at FROM dashboard_prompts ORDER BY id"
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["variables"] = json.loads(item["variables"] or "[]")
            result.append(item)
        return result

    def update_prompt(self, prompt_id: str, content: str) -> dict | None:
        current = self.conn.execute(
            "SELECT content FROM dashboard_prompts WHERE id = ?", (prompt_id,)
        ).fetchone()
        if not current:
            return None
        self.conn.execute(
            "INSERT INTO prompt_history (prompt_id, content) VALUES (?, ?)",
            (prompt_id, current["content"]),
        )
        self.conn.execute(
            "UPDATE dashboard_prompts SET content = ?, updated_at = ? WHERE id = ?",
            (content, app_now_iso(), prompt_id),
        )
        self.conn.commit()
        self.log_dashboard(None, "info", "prompts", f"Prompt updated: {prompt_id}")
        return self.conn.execute(
            "SELECT id, name, description, variables, content, updated_at FROM dashboard_prompts WHERE id = ?",
            (prompt_id,),
        ).fetchone()

    def get_prompt_history(self, prompt_id: str, limit: int = 10) -> list:
        return [dict(row) for row in self.conn.execute(
            "SELECT id, prompt_id, content, created_at FROM prompt_history WHERE prompt_id = ? ORDER BY id DESC LIMIT ?",
            (prompt_id, limit),
        ).fetchall()]

    def get_settings(self) -> dict:
        settings = {}
        for row in self.conn.execute("SELECT key, value, updated_at FROM dashboard_settings ORDER BY key").fetchall():
            try:
                settings[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                settings[row["key"]] = row["value"]
        return settings

    def update_settings(self, section: str, value) -> dict:
        self.conn.execute(
            """
            INSERT INTO dashboard_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (section, json.dumps(value), app_now_iso()),
        )
        self.conn.commit()
        self.log_dashboard(None, "info", "settings", f"Settings updated: {section}")
        return self.get_settings()

    def set_api_key_override(self, key_id: str, value: str):
        self.conn.execute(
            """
            INSERT INTO api_key_overrides (key_id, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key_id) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key_id, value, app_now_iso()),
        )
        self.conn.commit()
        self.log_dashboard(None, "info", "api-keys", f"API key override saved: {key_id}")

    def get_api_key_override(self, key_id: str) -> str | None:
        row = self.conn.execute("SELECT value FROM api_key_overrides WHERE key_id = ?", (key_id,)).fetchone()
        return row["value"] if row else None

    def close(self):
        self.conn.close()
