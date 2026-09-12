"""Configuration, read once from the environment."""
import os

from dotenv import load_dotenv

load_dotenv()


def _f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
CHANNEL_NAME = os.environ.get("AMEEN_CHANNEL", "ap-review")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = os.environ.get("AMEEN_MODEL", "anthropic/claude-sonnet-4-6")

SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")
SHEET_ID = os.environ.get("AMEEN_SHEET_ID", "")

L1_MAX = _f("AMEEN_L1_MAX", 1000)
L2_MAX = _f("AMEEN_L2_MAX", 10000)
L3_MAX = _f("AMEEN_L3_MAX", 50000)
PRICE_TOLERANCE = _f("AMEEN_PRICE_TOLERANCE", 0.02)

# Any extracted field below this is treated as unreadable and Ameen asks
# rather than guessing.
CONFIDENCE_FLOOR = _f("AMEEN_CONFIDENCE_FLOOR", 0.60)

DB_PATH = os.environ.get("AMEEN_DB", "ameen.db")
