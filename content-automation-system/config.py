import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

IS_VERCEL = bool(os.getenv("VERCEL"))
DATA_DIR = Path(os.getenv("APP_DATA_DIR", "/tmp/automation-data" if IS_VERCEL else BASE_DIR / "data"))

CONFIG = {
    "db_path":           str(Path(os.getenv("DB_PATH", DATA_DIR / "state.db"))),
    "cache_dir":         str(Path(os.getenv("CACHE_DIR", DATA_DIR / "cache"))),
    "nvidia_api_key": os.getenv("OPENROUTER_API_KEY", "") or os.getenv("NVIDIA_API_KEY", ""),
    "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
    "wordpress_url":     os.getenv("WORDPRESS_URL", ""),
    "wordpress_username": os.getenv("WORDPRESS_USERNAME", ""),
    "wordpress_password": os.getenv("WORDPRESS_APP_PASSWORD", ""),
    "ttapi_api_key":     os.getenv("TTAPI_API_KEY", ""),
}
