import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1] / "content-automation-system"
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))

google_credentials = os.getenv("GOOGLE_CREDENTIALS_JSON")
if google_credentials:
    credentials_path = Path("/tmp/google-credentials.json")
    credentials_path.write_text(google_credentials, encoding="utf-8")
    os.environ["GOOGLE_CREDENTIALS_PATH"] = str(credentials_path)

from main import app  # noqa: E402
