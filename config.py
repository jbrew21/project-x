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

# Watchlist: accounts known for inflammatory framing / engagement farming.
# The bot analyzes their TWEETS, not the accounts themselves.
# Balanced across political spectrum. Judge the content, not the person.
WATCHLIST = [
    # --- Right-leaning aggregator/commentary accounts ---
    "libsoftiktok",       # Libs of TikTok — curates content with inflammatory framing
    "EndWokeness",        # End Wokeness — culture war aggregator, 3.9M followers
    "catturd2",           # Catturd — MAGA shitposting, conspiracy theories
    "DCDraino",           # DC Draino — right-wing commentary, paid by X monetization
    "GuntherEagleman",    # Gunther Eagleman — engagement farming, inflammatory framing
    "bennyjohnson",       # Benny Johnson — right-wing content creator
    "jacksonhinklle",     # Jackson Hinkle — "MAGA communist", ~40% fake followers per Cyabra
    "stillgray",          # Ian Miles Cheong — conservative propagandist based in Malaysia

    # --- Left-leaning aggregator/commentary accounts ---
    "OccupyDemocrats",    # Occupy Democrats — hyperpartisan clickbait, false info flagged by PolitiFact
    "BrooklynDadDef",     # Brooklyn Dad Defiant — paid by Democratic PAC, engagement farming
    "MeidasTouch",        # MeidasTouch — left-wing commentary, inflammatory framing
    "BidenHQ",            # Biden campaign account — partisan engagement content
    "AccountableGOP",     # Accountable GOP — opposition research framing

    # --- Non-partisan / general engagement farmers ---
    "CollinRugg",         # Collin Rugg — Trending Politics, aggregates with outrage framing
    "MarioNawfal",        # Mario Nawfal — engagement farming, breaking news with spin
    "dom_lucre",          # Dom Lucre — conspiracy theories, engagement farming
    "WallStreetSilv",     # Wall Street Silver — pivoted from finance to culture war content
]
