"""
Google Sheets integration — appends one row per published article.

Row order: keyword | title | description | image_u1 | image_u2 | recipe_image
| pinterest_pin | rss_image | social_image | url | status

Requires:
  - credentials.json in the project root (downloaded from Google Cloud Console)
  - GOOGLE_SHEET_NAME set in .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DEFAULT_CREDENTIALS_PATH = Path(__file__).parent.parent / "credentials.json"


def _get_worksheet():
    # Read at call time — after dotenv is loaded
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "")

    credentials_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH", DEFAULT_CREDENTIALS_PATH))

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google credentials not found at {credentials_path}. "
            "Download it from Google Cloud Console → Service Accounts → Keys."
        )

    if not sheet_name:
        raise ValueError(
            "GOOGLE_SHEET_NAME is not set in .env. "
            "Add: GOOGLE_SHEET_NAME=automation_tool_pins"
        )

    print(f"[sheets] Using Google Sheet: {sheet_name}")

    import gspread
    from google.oauth2.service_account import Credentials

    creds  = Credentials.from_service_account_file(str(credentials_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open(sheet_name).get_worksheet(0)


def append_to_sheet(data: dict) -> bool:
    """
    Append one row to the Google Sheet.
    Returns True on success, False on failure (never raises — pipeline continues).

    Expected keys: keyword, title, description, image_u1, image_u2, recipe_image,
    pinterest_pin, rss_image, social_image, url
    """
    row = [
        data.get("keyword",     ""),
        data.get("title",       ""),
        data.get("description", ""),
        data.get("image_u1",    ""),
        data.get("image_u2",    ""),
        data.get("recipe_image", ""),
        data.get("pinterest_pin", ""),
        data.get("rss_image", ""),
        data.get("social_image", ""),
        data.get("url",         ""),
        "done",
    ]

    try:
        ws = _get_worksheet()
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[sheets] Saved to Google Sheet: {data.get('title', '')}")
        return True
    except FileNotFoundError as e:
        print(f"[sheets] Skipped — {e}")
        return False
    except ValueError as e:
        print(f"[sheets] Skipped — {e}")
        return False
    except Exception as e:
        print(f"[sheets] Failed to save to Google Sheet (non-fatal): {type(e).__name__}: {e}")
        return False
