import asyncio
import os
import httpx
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

try:
    from dotenv import load_dotenv as _load_dotenv
    _DOTENV_PATH = Path(__file__).parent.parent / ".env"
    def _reload_env():
        _load_dotenv(dotenv_path=_DOTENV_PATH, override=True)
except ImportError:
    def _reload_env():
        pass

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free OpenRouter models that support system prompts and produce JSON content.
# Non-reasoning models only — reasoning models burn tokens on internal thinking.
# OpenRouter caps the array at 3 — primary + 2 fallbacks.
FALLBACK_MODELS = [
    "openai/gpt-oss-20b:free",     # fastest (~1s), supports system role
    "openai/gpt-oss-120b:free",    # reliable backup, ~6s
    "z-ai/glm-4.5-air:free",       # last resort (reasoning, slow but works)
]

try:
    from services.telegram_notifier import send_telegram_message
except Exception:
    def send_telegram_message(text: str, chat_id: str | None = None) -> bool:
        return False


class APIKeyFallbackError(Exception):
    def __init__(self, reason: str, original: Exception | None = None):
        super().__init__(reason)
        self.reason = reason
        self.original = original


@dataclass
class APIKeyFailure:
    masked_key: str
    reason: str


_last_successful_key_index = 0


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return "(empty)"
    if len(api_key) <= 12:
        return "****"
    return f"{api_key[:5]}-****{api_key[-4:]}"


def _split_api_keys(value: str) -> list[str]:
    parts = re.split(r"[\n,]+", value or "")
    return [part.strip() for part in parts if part.strip()]


def load_openrouter_api_keys(explicit_key: str = "") -> list[str]:
    keys: list[str] = []
    if explicit_key.strip():
        keys.append(explicit_key.strip())
    keys.extend(_split_api_keys(os.getenv("OPENROUTER_API_KEYS", "")))
    single_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if single_key:
        keys.append(single_key)

    unique: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if key not in seen:
            unique.append(key)
            seen.add(key)
    return unique


def _ordered_api_keys(api_keys: Iterable[str]) -> list[str]:
    global _last_successful_key_index
    keys = list(api_keys)
    if not keys:
        return []
    start = _last_successful_key_index % len(keys)
    return keys[start:] + keys[:start]


def _set_last_successful_key(api_keys: list[str], api_key: str) -> None:
    global _last_successful_key_index
    try:
        _last_successful_key_index = api_keys.index(api_key)
    except ValueError:
        _last_successful_key_index = 0


def _fallback_reason_from_status(status_code: int) -> str | None:
    if status_code == 401:
        return "API key invalid"
    if status_code in (402, 429):
        return "API quota exceeded"
    return None


def _notify_key_switched(reason: str, next_key: str | None = None, keyword: str = "") -> None:
    lines = [
        "⚠️ API Key Switched",
        f"Reason: {reason}",
    ]
    if keyword:
        lines.append(f"Keyword: {keyword}")
    if next_key:
        lines.append(f"Next key: {mask_api_key(next_key)}")
    try:
        send_telegram_message("\n".join(lines))
    except Exception as exc:
        print(f"[llm] Telegram key-switch alert failed: {type(exc).__name__}: {exc}")


def _notify_all_keys_failed(keyword: str, reason: str) -> None:
    lines = [
        "❌ All API Keys Failed",
    ]
    if keyword:
        lines.append(f"Keyword: {keyword}")
    lines.append(f"Reason: {reason}")
    try:
        send_telegram_message("\n".join(lines))
    except Exception as exc:
        print(f"[llm] Telegram all-keys-failed alert failed: {type(exc).__name__}: {exc}")


async def generate_with_fallback(
    payload: dict,
    api_keys: list[str] | None = None,
    base_url: str | None = None,
    keyword: str = "",
    timeout_seconds: float | None = None,
) -> dict:
    all_keys = api_keys or load_openrouter_api_keys()
    if not all_keys:
        raise RuntimeError("No OpenRouter API keys configured")

    ordered_keys = _ordered_api_keys(all_keys)
    request_url = base_url or os.getenv("LLM_BASE_URL", OPENROUTER_URL)
    read_timeout = timeout_seconds or float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    timeout = httpx.Timeout(read_timeout, connect=30.0, read=read_timeout, write=60.0, pool=30.0)
    failures: list[APIKeyFailure] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for key_index, api_key in enumerate(ordered_keys):
            masked = mask_api_key(api_key)
            print(f"[llm] Trying OpenRouter key {masked}")
            try:
                response = await client.post(
                    request_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://chocokitchen.com"),
                        "X-OpenRouter-Title": os.getenv("OPENROUTER_APP_NAME", "Content Automation"),
                    },
                    json=payload,
                )
            except (httpx.TimeoutException, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
                reason = "AI timeout"
                failures.append(APIKeyFailure(masked, reason))
                next_key = ordered_keys[key_index + 1] if key_index + 1 < len(ordered_keys) else None
                print(f"[llm] Key {masked} failed: {reason}")
                if next_key:
                    print(f"[llm] Switching to {mask_api_key(next_key)}")
                    _notify_key_switched(reason, next_key, keyword)
                    continue
                break
            except httpx.TransportError as exc:
                print(f"[llm] Network error with key {masked}: {type(exc).__name__}: {exc}")
                raise

            fallback_reason = _fallback_reason_from_status(response.status_code)
            if fallback_reason:
                failures.append(APIKeyFailure(masked, fallback_reason))
                next_key = ordered_keys[key_index + 1] if key_index + 1 < len(ordered_keys) else None
                print(f"[llm] Key {masked} failed: HTTP {response.status_code} ({fallback_reason})")
                if next_key:
                    print(f"[llm] Switching to {mask_api_key(next_key)}")
                    _notify_key_switched(fallback_reason, next_key, keyword)
                    continue
                break

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                print(f"[llm] HTTP error {response.status_code}: {response.text[:300]}")
                raise

            try:
                body = response.json()
            except ValueError as exc:
                reason = "Invalid AI response"
                failures.append(APIKeyFailure(masked, reason))
                next_key = ordered_keys[key_index + 1] if key_index + 1 < len(ordered_keys) else None
                print(f"[llm] Key {masked} failed: {reason}")
                if next_key:
                    print(f"[llm] Switching to {mask_api_key(next_key)}")
                    _notify_key_switched(reason, next_key, keyword)
                    continue
                break
                raise APIKeyFallbackError(reason, exc) from exc

            if "error" in body and not body.get("choices"):
                err = body["error"]
                code = err.get("code") if isinstance(err, dict) else None
                msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                fallback_reason = _fallback_reason_from_status(int(code)) if str(code).isdigit() else None
                if fallback_reason:
                    failures.append(APIKeyFailure(masked, fallback_reason))
                    next_key = ordered_keys[key_index + 1] if key_index + 1 < len(ordered_keys) else None
                    print(f"[llm] Key {masked} failed: provider {code} ({fallback_reason})")
                    if next_key:
                        print(f"[llm] Switching to {mask_api_key(next_key)}")
                        _notify_key_switched(fallback_reason, next_key, keyword)
                        continue
                    break
                raise RuntimeError(f"OpenRouter provider error {code}: {msg[:200]}")

            choices = body.get("choices") or []
            content = ((choices[0].get("message") or {}).get("content") if choices else "") or ""
            if not choices or not content.strip():
                reason = "Empty response"
                failures.append(APIKeyFailure(masked, reason))
                next_key = ordered_keys[key_index + 1] if key_index + 1 < len(ordered_keys) else None
                print(f"[llm] Key {masked} failed: {reason}")
                if next_key:
                    print(f"[llm] Switching to {mask_api_key(next_key)}")
                    _notify_key_switched(reason, next_key, keyword)
                    continue
                break

            _set_last_successful_key(all_keys, api_key)
            print(f"[llm] OpenRouter key {masked} succeeded")
            return body

    reason = failures[-1].reason if failures else "All keys exhausted"
    _notify_all_keys_failed(keyword, "All keys exhausted")
    failure_summary = "; ".join(f"{f.masked_key}: {f.reason}" for f in failures) or reason
    raise RuntimeError(f"All OpenRouter API keys failed: {failure_summary}")


class LLMClient:
    def __init__(self, api_key: str = "", model: str = ""):
        # Re-read .env on every instantiation so key changes take effect
        # without restarting the Celery worker.
        _reload_env()
        self.model    = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
        self.api_keys = load_openrouter_api_keys(api_key)
        self.api_key  = self.api_keys[0] if self.api_keys else ""
        self.base_url = os.getenv("LLM_BASE_URL", OPENROUTER_URL)

    def rotate_after_invalid_response(self, keyword: str = "") -> None:
        global _last_successful_key_index
        if len(self.api_keys) < 2:
            return
        failed_key = self.api_keys[_last_successful_key_index % len(self.api_keys)]
        _last_successful_key_index = (_last_successful_key_index + 1) % len(self.api_keys)
        next_key = self.api_keys[_last_successful_key_index]
        print(
            f"[llm] Key {mask_api_key(failed_key)} returned invalid AI output; "
            f"switching to {mask_api_key(next_key)}"
        )
        _notify_key_switched("Invalid AI response", next_key, keyword)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: str = "",
        keyword: str = "",
    ) -> str:
        print(f"[llm] Using model: {self.model} via {self.base_url[:40]}")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # OpenRouter caps the models array at 3 items.
        # Primary first, then up to 2 fallbacks.
        models_chain = ([self.model] + [m for m in FALLBACK_MODELS if m != self.model])[:3]

        max_attempts = 3
        payload = {
            "model":       self.model,
            "models":      models_chain,
            "messages":    messages,
            "temperature": temperature,
            "max_tokens":  max_tokens,
        }

        for attempt in range(max_attempts):
            try:
                body = await generate_with_fallback(
                    payload,
                    api_keys=self.api_keys,
                    base_url=self.base_url,
                    keyword=keyword,
                )
                content = (body["choices"][0].get("message") or {}).get("content")
                if content:
                    return content
            except httpx.TransportError as e:
                if attempt == max_attempts - 1:
                    print(f"[llm] Network failure after {max_attempts} attempts: {type(e).__name__}: {e}")
                    raise
                delay = 8 * (attempt + 1)
                print(f"[llm] {type(e).__name__}: {e} — retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(delay)
            except RuntimeError:
                raise

        raise RuntimeError("LLM request failed without a response")

    def parse_json(self, response: str) -> Dict:
        # Strip markdown fences
        clean = re.sub(r"```(?:json)?\s*|\s*```", "", response.strip())

        # Slice to the outermost JSON object — ignore any leading/trailing prose
        start = clean.find("{")
        end   = clean.rfind("}") + 1
        if start != -1 and end > start:
            clean = clean[start:end]

        # Attempt 1: strict parse
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # Attempt 2: permissive (allows control chars in strings)
        try:
            return json.loads(clean, strict=False)
        except json.JSONDecodeError:
            pass

        # Attempt 3: raw_decode — stops at the first valid object even if garbage follows
        try:
            parsed, _ = json.JSONDecoder(strict=False).raw_decode(clean)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        raise ValueError(f"Failed to parse JSON from LLM response: {response[:400]}")
