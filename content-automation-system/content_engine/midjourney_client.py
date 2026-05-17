"""
Midjourney image generation via ttapi.io.

Full flow:
    1. POST /midjourney/v1/imagine          → submit prompt, get jobId
    2. GET  /midjourney/v1/fetch?jobId=...  → poll until progress == "100"
    3. POST /midjourney/v1/action           → upscale U1, get new jobId
    4. GET  /midjourney/v1/fetch?jobId=...  → poll upscale until done
    5. Return final image URL
"""

import os
import re
import time
import asyncio
import requests
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

TTAPI_BASE    = os.getenv("TTAPI_BASE_URL", "https://hold.ttapi.io/midjourney/v1").rstrip("/")
TTAPI_HOLD_BASE = TTAPI_BASE.split("/midjourney/", 1)[0]
POLL_INTERVAL = 10    # seconds between polls
POLL_TIMEOUT  = 600   # 10 minutes max per step
_MODE_CACHE: tuple[str, float] | None = None
_LAST_ERROR: str | None = None

TTAPI_PROMPT_REPLACEMENTS = (
    (r"\bchicken\s+breast(s)?\b", "chicken fillet"),
    (r"\bturkey\s+breast(s)?\b", "turkey fillet"),
    (r"\bduck\s+breast(s)?\b", "duck fillet"),
    (r"\bbreast(s)?\b", "fillet"),
)


# ── Prompt builder ────────────────────────────────────────────────────

PROMPT_SYSTEM = """\
You are a food enthusiast, amateur photographer and an expert generative digital artist specializing in creating Midjourney prompts for single amateur photographic main plate dish images. When provided with a full recipe in any language, generate exactly one refined descriptive text prompt in English that meets the following criteria:

The prompt must depict a single vivid, enticing, and mouth-watering main plate dish in an amateur photorealistic homemade presentation in a normal kitchen setting style as though it were captured with an iPhone 15 Pro. Emphasize an amateur yet authentic vibe that showcases vibrant colors, intricate textures, and a juicy, mouthwatering appeal. The description should depict the dish presented in a simple home setting with natural lighting, captured as a close-up from a human eye-level side angle. The background should be real, clear, and uncluttered, with no extra ingredients or rustic elements. The prompt should start with

amateur photo with interesting details and texture from Reddit taken with iPhone 15 Pro that hooks users for a juicy, mouthwatering

then be immediately followed by the title of the recipe (translate it) write it in English regardless of the recipe's original language.

If the recipe indicates that the dish's interior is an important visual element—for example, if it is a layered cake, pie, stuffed dish, or any dish designed to be viewed with a cut-open or sliced presentation—incorporate a depiction of the visible interior. For recipes like cakes or pies, show a slice rather than the whole item to highlight appealing layers, textures, and fillings, ensuring that the cross-sectional details harmonize with the overall presentation. Also, ensure that any language with potentially sexual intent is replaced with neutral terms; for example, use "unveiling" instead of "revealing."

Ensure that the final output focuses solely on generating a single, clearly defined main dish image with moderate detail that creates a strong visual representation.

Ensure handling of interiors (using neutral terms like "showing," "displaying," or "featuring" if needed, but not "revealing")

provide the Midjourney prompt in English directly. Do not use double quotations.
Double-check that the word "revealing" is absent
-keep your writing style simple and concise
-use clear and straightforward language
-steer clear of cliches and metaphors
-at the end add this parameters --s 100 --v 7 --ar 10:11\
"""


def build_image_prompt(keyword: str, article_title: str, article_content: str = "") -> str:
    """Use LLM to generate a Midjourney food-photography prompt."""
    from .llm_client import LLMClient

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("NVIDIA_API_KEY", "")
    dish    = article_title or keyword
    content_snippet = article_content[:3000] if article_content else dish

    user_message = (
        f"Recipe title: {dish}\n\n"
        f"Article/recipe content:\n{content_snippet}"
    )

    full_prompt = f"{PROMPT_SYSTEM}\n\n{user_message}"

    try:
        llm = LLMClient(api_key)
        raw = asyncio.run(llm.generate(full_prompt, temperature=0.3, max_tokens=300))
        # Strip quotes and ensure no non-ASCII characters
        cleaned = raw.strip().strip('"').strip("'")
        cleaned = re.sub(r'[^\x00-\x7F]', '', cleaned)
        # Safety: replace "revealing" just in case
        cleaned = cleaned.replace("revealing", "showing")
        print(f"[image_prompt] AI-generated prompt: {cleaned[:150]}...")
        return cleaned[:900]
    except Exception as e:
        print(f"[image_prompt] LLM failed ({e}) — using fallback prompt")
        fallback = (
            f"amateur photo with interesting details and texture from Reddit "
            f"taken with iPhone 15 Pro that hooks users for a juicy, mouthwatering "
            f"{dish}, close-up at eye-level, natural kitchen lighting, "
            f"simple uncluttered background, homemade presentation, single dish only "
            f"--s 100 --v 7 --ar 10:11"
        )
        return re.sub(r'[^\x00-\x7F]', '', fallback)[:900]


# ── Auth ──────────────────────────────────────────────────────────────

def _headers() -> dict:
    """TT-API-KEY is the correct TTAPI auth header (NOT Bearer)."""
    return {
        "TT-API-KEY":    os.getenv("TTAPI_API_KEY", ""),
        "Content-Type":  "application/json",
    }

def _masked_key() -> str:
    key = os.getenv("TTAPI_API_KEY", "")
    return f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "(not set)"


def _active_mode() -> str:
    """Return the current TTAPI Hold Account mode: fast, relax, or turbo."""
    configured = os.getenv("TTAPI_MODE", "").strip().lower()
    if configured in {"fast", "relax", "turbo"}:
        return configured

    global _MODE_CACHE
    now = time.time()
    if _MODE_CACHE and now - _MODE_CACHE[1] < 5:
        return _MODE_CACHE[0]

    mode = "fast"
    try:
        resp = requests.get(
            f"{TTAPI_HOLD_BASE}/account/list",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        accounts = resp.json().get("data") or []
        active = next((account for account in accounts if account.get("useMode") in {1, 2, 3}), None)
        use_mode = active.get("useMode") if isinstance(active, dict) else None
        mode = {1: "relax", 2: "fast", 3: "turbo"}.get(use_mode, mode)
        print(f"TTAPI active mode: {mode} (useMode={use_mode})")
    except Exception as exc:
        print(f"TTAPI active mode lookup failed; using {mode}: {type(exc).__name__}: {exc}")

    _MODE_CACHE = (mode, now)
    return mode


def _sanitize_ttapi_prompt(prompt: str) -> str:
    cleaned = prompt or ""
    for pattern, replacement in TTAPI_PROMPT_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:900]


# ── Step 1: Submit imagine ────────────────────────────────────────────

def _submit_imagine(prompt: str) -> str | None:
    global _LAST_ERROR
    _LAST_ERROR = None
    url = f"{TTAPI_BASE}/imagine"
    prompt = _sanitize_ttapi_prompt(prompt)
    print("STEP 1: Sending imagine request")
    print(f"  URL   : {url}")
    print(f"  Key   : {_masked_key()}")
    print(f"  Prompt: {prompt[:120]}")

    try:
        mode = _active_mode()
        modes = [mode]
        fallback_mode = {"fast": "relax", "relax": "fast"}.get(mode)
        if fallback_mode:
            modes.append(fallback_mode)

        resp = None
        for index, request_mode in enumerate(modes):
            print(f"  Mode  : {request_mode}")
            resp = requests.post(
                url,
                headers=_headers(),
                json={"prompt": prompt, "mode": request_mode},
                timeout=30,
            )
            print(f"  HTTP  : {resp.status_code}")
            print(f"  Body  : {resp.text[:400]}")
            try:
                body = resp.json()
                api_message = body.get("message") or body.get("error") or resp.text[:200]
            except Exception:
                api_message = resp.text[:200]
            if resp.status_code != 400 or "No available accounts" not in resp.text or index == len(modes) - 1:
                break
            print(f"  No account available for {request_mode}; retrying with {modes[index + 1]}")

        if resp is None:
            return None

        if resp.status_code == 401:
            print("MIDJOURNEY FAILED — 401 Unauthorized: check TTAPI_API_KEY in .env")
            _LAST_ERROR = "TTAPI 401 Unauthorized: check TTAPI_API_KEY in .env"
            return None
        if resp.status_code == 400:
            print("MIDJOURNEY FAILED — 400 Bad Request: invalid prompt or params")
            _LAST_ERROR = f"TTAPI 400: {api_message}"
            return None
        if resp.status_code == 402:
            print("MIDJOURNEY FAILED — 402 Payment Required: insufficient TTAPI balance")
            _LAST_ERROR = f"TTAPI 402: {api_message}"
            return None
        if resp.status_code == 404:
            print(f"MIDJOURNEY FAILED — 404 Not Found: wrong endpoint {url}")
            _LAST_ERROR = f"TTAPI 404 Not Found: wrong endpoint {url}"
            return None
        resp.raise_for_status()

        job_id = resp.json().get("data", {}).get("jobId")
        print(f"JOB ID: {job_id}")
        return job_id

    except requests.exceptions.ConnectionError as e:
        print(f"MIDJOURNEY FAILED — ConnectionError: {e}")
        print(f"  Cannot reach: {url}")
        print(f"  Check: internet connection, VPN, or firewall blocking {TTAPI_BASE}")
        _LAST_ERROR = f"TTAPI connection error: {e}"
        return None
    except requests.exceptions.Timeout:
        print("MIDJOURNEY FAILED — Request timed out after 30s")
        _LAST_ERROR = "TTAPI request timed out after 30s"
        return None
    except Exception as e:
        print(f"MIDJOURNEY FAILED — Unexpected error: {type(e).__name__}: {e}")
        _LAST_ERROR = f"TTAPI unexpected error: {type(e).__name__}: {e}"
        return None


# ── Step 2 & 4: Poll GET until progress == "100" ─────────────────────

def _poll(job_id: str, label: str = "") -> dict | None:
    """
    GET /midjourney/v1/fetch?jobId=...
    Polls every POLL_INTERVAL seconds until progress == "100".
    """
    url        = f"{TTAPI_BASE}/fetch"
    deadline   = time.time() + POLL_TIMEOUT
    poll_count = 0

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        poll_count += 1

        try:
            resp = requests.get(
                url,
                headers=_headers(),
                params={"jobId": job_id},
                timeout=30,
            )
            print(f"  Fetch HTTP: {resp.status_code}")
            resp.raise_for_status()
            body = resp.json()
            data = body.get("data", {})
        except Exception as e:
            print(f"  Poll #{poll_count} error: {e} — retrying")
            continue

        progress = str(data.get("progress", "0"))
        status = str(body.get("status") or data.get("status") or "").upper()

        if label == "U1 upscale":
            print(f"Upscale progress: {progress}% (poll #{poll_count})")
        else:
            print(f"Progress: {progress}% (poll #{poll_count})")

        if progress == "100" or status in {"SUCCESS", "COMPLETED", "DONE"}:
            print("Upscale complete" if label == "U1 upscale" else "Imagine complete")
            return data

        if status == "FAILED":
            print(f"MIDJOURNEY FAILED — API returned FAILED: {body.get('message', '')}")
            return None

        if poll_count >= 60:
            print("MIDJOURNEY FAILED — Timed out after 60 polls (10 min)")
            return None

    print("MIDJOURNEY FAILED — Deadline exceeded")
    return None


# ── URL extraction ────────────────────────────────────────────────────

IMAGE_URL_KEYS = {
    "cdnImage",
    "discordImage",
    "imageUrl",
    "imageURL",
    "image_url",
    "url",
    "proxy_url",
    "proxyUrl",
}


def _looks_like_image_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if not value.startswith(("http://", "https://")):
        return False
    lowered = value.lower().split("?", 1)[0]
    return (
        lowered.endswith((".png", ".jpg", ".jpeg", ".webp"))
        or "cdn.discordapp.com" in lowered
        or "media.discordapp.net" in lowered
        or "mjcdn" in lowered
        or "ttapi" in lowered
    )


def _walk_image_urls(value: object, path: str = "data") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []

    if isinstance(value, dict):
        for key, nested in value.items():
            next_path = f"{path}.{key}"
            if key in IMAGE_URL_KEYS and _looks_like_image_url(nested):
                found.append((next_path, nested))
            found.extend(_walk_image_urls(nested, next_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found.extend(_walk_image_urls(nested, f"{path}[{index}]"))
    elif _looks_like_image_url(value):
        found.append((path, value))

    return found


def _extract_url(data: dict) -> str | None:
    """Extract image URL from TTAPI completed job data across response variants."""
    print(f"  Response keys: {list(data.keys())}")

    for key in ("cdnImage", "discordImage"):
        url = data.get(key)
        if _looks_like_image_url(url):
            print(f"  Source: data.{key}")
            return url

    candidates = _walk_image_urls(data)
    if candidates:
        source, url = candidates[0]
        print(f"  Source: {source}")
        return url

    print(f"  MIDJOURNEY FAILED — no image URL found. Full data: {data}")
    return None


def _masked_url(url: str | None) -> str:
    if not url:
        return "-"
    return url[:42] + "..." if len(url) > 45 else url


def _download_probe_image(url: str) -> Image.Image | None:
    try:
        resp = requests.get(url, timeout=25)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception as exc:
        print(f"[image_select] Could not inspect image {_masked_url(url)}: {type(exc).__name__}: {exc}")
        return None


def _seam_score(img: Image.Image, axis: str) -> tuple[float, float]:
    gray = ImageOps.grayscale(img.resize((320, 320), Image.Resampling.BICUBIC))
    if axis == "vertical":
        a = gray.crop((156, 0, 160, 320))
        b = gray.crop((160, 0, 164, 320))
        diff = ImageChops.difference(a, b)
        samples = [sum(diff.crop((0, y, 4, y + 1)).getdata()) / 4 for y in range(320)]
    else:
        a = gray.crop((0, 156, 320, 160))
        b = gray.crop((0, 160, 320, 164))
        diff = ImageChops.difference(a, b)
        samples = [sum(diff.crop((x, 0, x + 1, 4)).getdata()) / 4 for x in range(320)]

    mean = sum(samples) / max(1, len(samples))
    continuity = sum(1 for value in samples if value > 28) / max(1, len(samples))
    return mean, continuity


def _image_quality_score(img: Image.Image) -> dict:
    probe = ImageOps.exif_transpose(img).convert("RGB").resize((360, 360), Image.Resampling.BICUBIC)
    stat = ImageStat.Stat(probe)
    brightness = sum(stat.mean) / 3
    contrast = sum(stat.stddev) / 3
    saturation = ImageStat.Stat(probe.convert("HSV")).mean[1]
    sharpness = ImageStat.Stat(probe.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]
    brightness_penalty = abs(brightness - 145) * 0.25
    score = saturation * 0.45 + contrast * 0.55 + sharpness * 1.8 - brightness_penalty
    return {
        "score": round(score, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "saturation": round(saturation, 2),
        "sharpness": round(sharpness, 2),
    }


def _inspect_single_image(url: str) -> tuple[bool, dict]:
    img = _download_probe_image(url)
    if img is None:
        return False, {"score": 0, "error": "download_failed"}

    vertical_mean, vertical_continuity = _seam_score(img, "vertical")
    horizontal_mean, horizontal_continuity = _seam_score(img, "horizontal")

    vertical_panel = vertical_mean > 20 and vertical_continuity > 0.42
    horizontal_panel = horizontal_mean > 20 and horizontal_continuity > 0.42
    looks_grid = vertical_panel or horizontal_panel
    metrics = _image_quality_score(img)
    metrics.update({
        "grid_check": looks_grid,
        "vertical_seam_mean": round(vertical_mean, 2),
        "vertical_seam_continuity": round(vertical_continuity, 3),
        "horizontal_seam_mean": round(horizontal_mean, 2),
        "horizontal_seam_continuity": round(horizontal_continuity, 3),
    })

    print(
        "[image_select] "
        f"grid_check={looks_grid} "
        f"score={metrics['score']} "
        f"vertical=({vertical_mean:.1f},{vertical_continuity:.2f}) "
        f"horizontal=({horizontal_mean:.1f},{horizontal_continuity:.2f}) "
        f"url={_masked_url(url)}"
    )
    return looks_grid, metrics


def _select_single_images(upscaled_urls: dict[int, str | None], grid_data: dict) -> tuple[str | None, str | None, dict]:
    ranked: list[dict] = []
    rejected: list[int] = []

    for position in (1, 2, 3, 4):
        url = upscaled_urls.get(position)
        if not url:
            continue
        looks_grid, metrics = _inspect_single_image(url)
        if looks_grid:
            rejected.append(position)
            print(f"[image_select] U{position} rejected because it looks like a multi-image grid")
            continue
        ranked.append({"position": position, "url": url, **metrics})
        print(f"[image_select] U{position} accepted as a single image with score {metrics.get('score')}")

    if ranked:
        ranked.sort(key=lambda item: float(item.get("score") or 0), reverse=True)
        hero = ranked[0]["url"]
        secondary = ranked[1]["url"] if len(ranked) > 1 else ranked[0]["url"]
        return hero, secondary, {
            "accepted": [item["position"] for item in ranked],
            "rejected": rejected,
            "ranked_images": ranked,
            "best_image": ranked[0],
            "second_best_image": ranked[1] if len(ranked) > 1 else ranked[0],
            "fallback": False,
        }

    fallback = upscaled_urls.get(1) or _extract_url(grid_data)
    print("[image_select] No clean single image found — falling back to U1/grid image")
    return fallback, fallback, {
        "accepted": [],
        "rejected": rejected,
        "ranked_images": [],
        "best_image": {"position": 1, "url": fallback, "score": 0},
        "second_best_image": {"position": 1, "url": fallback, "score": 0},
        "fallback": True,
    }


# ── Step 3: Upscale (generic — U1 or U2) ─────────────────────────────

def _upscale(grid_job_id: str, action: str) -> str | None:
    """Submit an upscale action (upsample1 or upsample2), return new jobId."""
    url   = f"{TTAPI_BASE}/action"
    label = "U" + action.replace("upsample", "")
    print(f"Requesting {label} upscale — action: {action}")
    print(f"  URL       : {url}")
    print(f"  Parent JOB: {grid_job_id}")

    for attempt in range(1, 4):
        try:
            resp = requests.post(
                url,
                headers=_headers(),
                json={"jobId": grid_job_id, "action": action},
                timeout=75,
            )
            print(f"  HTTP  : {resp.status_code}")
            print(f"  Body  : {resp.text[:400]}")
            resp.raise_for_status()

            upscale_job_id = resp.json().get("data", {}).get("jobId")
            print(f"{label} JOB ID: {upscale_job_id}")
            return upscale_job_id

        except Exception as e:
            print(f"MIDJOURNEY FAILED — {label} upscale attempt {attempt}/3 error: {type(e).__name__}: {e}")
            if attempt < 3:
                time.sleep(5 * attempt)

    return None


# ── Public interface ──────────────────────────────────────────────────

def generate_midjourney_image(prompt: str) -> dict:
    """
    Full flow: imagine → poll grid → U1-U4 upscale → inspect → return best single-image URLs.

    Returns dict:
        {"image_url": u1_url, "image_url_2": u2_url}

    Either URL can be None if that upscale failed.
    Both None means full failure — pipeline continues safely.
    """
    api_key = os.getenv("TTAPI_API_KEY")
    if not api_key:
        print("MIDJOURNEY FAILED — TTAPI_API_KEY not set in .env")
        return {"image_url": None, "image_url_2": None}

    print(f"TTAPI key: {_masked_key()}")

    # 1. Submit imagine
    grid_job_id = _submit_imagine(prompt)
    if not grid_job_id:
        return {"image_url": None, "image_url_2": None, "error": _LAST_ERROR}

    # 2. Poll grid until complete
    grid_data = _poll(grid_job_id, label="imagine")
    if not grid_data:
        return {"image_url": None, "image_url_2": None}

    # 3. Upscale positions 1-4 in parallel, then choose the first clean
    # single-photo image. Some providers return a 2-up or 4-up contact sheet
    # even after an upscale; those are rejected for hero/pin use.
    print("Upscaling U1, U2, U3 and U4 in parallel...")

    def _upscale_and_poll(position: int) -> str | None:
        job_id = _upscale(grid_job_id, f"upsample{position}")
        if not job_id:
            return None
        data = _poll(job_id, label=f"U{position} upscale")
        return _extract_url(data) if data else None

    upscaled_urls: dict[int, str | None] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_upscale_and_poll, position): position for position in (1, 2, 3, 4)}
        for future in as_completed(futures):
            position = futures[future]
            try:
                upscaled_urls[position] = future.result()
            except Exception as exc:
                print(f"U{position} upscale failed: {type(exc).__name__}: {exc}")
                upscaled_urls[position] = None

    u1_url, u2_url, selection = _select_single_images(upscaled_urls, grid_data)

    print(f"Selected hero URL: {u1_url}")
    print(f"Selected secondary URL: {u2_url}")
    print(f"Image selection: {selection}")
    return {
        "image_url": u1_url,
        "image_url_2": u2_url,
        "best_image": u1_url,
        "second_best_image": u2_url,
        "image_selection": selection,
        "all_upscaled_urls": {f"u{pos}": url for pos, url in sorted(upscaled_urls.items())},
    }


# ── Standalone test ───────────────────────────────────────────────────

def test_midjourney():
    """Run standalone to verify TTAPI connection before pipeline."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available; rely on env vars already set

    prompt = "chocolate cake on white ceramic plate, professional food photography, soft golden light"
    print(f"\nTesting TTAPI Midjourney...")
    print(f"Prompt: {prompt}\n")

    result = generate_midjourney_image(prompt)
    u1 = result.get("image_url")
    u2 = result.get("image_url_2")

    print("\n" + "="*50)
    if u1 or u2:
        print("✅ SUCCESS")
        print(f"U1: {u1}")
        print(f"U2: {u2}")
    else:
        print("❌ FAILED — no image URLs returned")
        print("Check the logs above for the specific error")
    print("="*50)
    return result


if __name__ == "__main__":
    test_midjourney()
