import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR / "content-automation-system"

if not (PROJECT_DIR / "main.py").is_file():
    raise RuntimeError(
        "FastAPI app not found. Expected content-automation-system/main.py. "
        "The content-automation-system directory is missing from this checkout; "
        "commit it as regular source files or configure a real git submodule."
    )

os.chdir(PROJECT_DIR)
sys.path[:0] = [str(PROJECT_DIR), str(ROOT_DIR)]

google_credentials = os.getenv("GOOGLE_CREDENTIALS_JSON")
if google_credentials:
    credentials_path = Path("/tmp/google-credentials.json")
    credentials_path.write_text(google_credentials, encoding="utf-8")
    os.environ["GOOGLE_CREDENTIALS_PATH"] = str(credentials_path)

from main import app  # noqa: E402
