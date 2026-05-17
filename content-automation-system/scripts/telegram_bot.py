from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.telegram_dashboard_bot import poll_telegram_commands


if __name__ == "__main__":
    poll_telegram_commands()
