import os
from dotenv import load_dotenv

load_dotenv()

# X/Twitter API credentials
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Bot settings
BOT_USERNAME = os.getenv("BOT_USERNAME", "ragebaittracker")
DAILY_SCAN_HOUR = int(os.getenv("DAILY_SCAN_HOUR", "9"))
DAILY_SCAN_MINUTE = int(os.getenv("DAILY_SCAN_MINUTE", "0"))
MENTION_POLL_INTERVAL_SECONDS = int(os.getenv("MENTION_POLL_INTERVAL_SECONDS", "30"))

# Known ragebait accounts to monitor (add X usernames without @)
# These are placeholders — populate with real accounts you want to track
WATCHLIST = [
    # "example_account_1",
    # "example_account_2",
]
