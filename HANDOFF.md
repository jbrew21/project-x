# Ragebait Tracker — Deployment Handoff for Brijesh

## What This Is

Ragebait Tracker (@ragetrack on X) is an AI bot built by Newsreel that:
1. **Mention responder**: Anyone tags @ragetrack on a tweet → bot replies with a ragebait rating (1-10) and explanation
2. **Daily thread**: Every day at 9am UTC, searches X for the worst ragebait tweets and posts a thread rating them

It needs to run **24/7** as a background process. Currently it only runs when Jack's Mac is open, which is the main problem.

## Repo

**GitHub**: https://github.com/jbrew21/project-x
**Branch**: `claude/ragebait-tracker-bot-zUwb5`

## Tech Stack

- **Python 3.11** (MUST be 3.11 — Python 3.13+ removed the `imghdr` module which tweepy needs. There's a shim file `imghdr.py` as a fallback but 3.11 is cleanest.)
- **tweepy** — X API v2 client
- **anthropic** — Claude AI API (Haiku model for fast tweet analysis)
- **python-dotenv** — env var loading
- **schedule** — daily scan scheduling

## The Problem: Render Deploy is Broken

A Render background worker was set up but crashed with exit code 127. Issues:

1. **Python version**: Render defaulted to Python 3.14, which breaks tweepy. Fix: set `PYTHON_VERSION=3.11.0` as an environment variable (already added to `render.yaml` but may need to be set manually in Render dashboard too).

2. **Environment variables needed** (all must be set in Render's Environment tab):
   ```
   PYTHON_VERSION=3.11.0
   X_API_KEY=<from X Developer Portal>
   X_API_SECRET=<from X Developer Portal>
   X_ACCESS_TOKEN=<from X Developer Portal>
   X_ACCESS_TOKEN_SECRET=<from X Developer Portal>
   X_BEARER_TOKEN=<from X Developer Portal>
   ANTHROPIC_API_KEY=<from Anthropic Console>
   BOT_USERNAME=ragetrack
   MENTION_POLL_INTERVAL_SECONDS=15
   DAILY_SCAN_HOUR=9
   DAILY_SCAN_MINUTE=0
   ```

3. **Service config**:
   - Type: Background Worker (NOT web service)
   - Build command: `pip install -r requirements.txt`
   - Start command: `python main.py`

4. **X API write permissions**: The Access Token must be generated AFTER setting User Authentication to "Read and Write" in the X Developer Portal (Apps → your app → User authentication settings). If you get 403 errors when posting, the token was generated with read-only permissions and needs to be regenerated.

## Architecture

```
main.py              → Entry point. Runs daily scheduler (background thread) + mention responder (foreground)
ai_analyzer.py       → Claude API integration. Loads ragebait_knowledge.md as the AI's "brain"
twitter_client.py    → X API v2 wrapper (post tweets, read mentions, search, get user tweets)
daily_scanner.py     → Searches X + scans watchlist accounts, posts daily thread
mention_responder.py → Polls for @ragetrack mentions every 15s, replies with AI analysis
config.py            → API keys, bot settings, watchlist of 17 accounts
ragebait_knowledge.md → Comprehensive knowledge base (research, scoring rubric, tactics)
imghdr.py            → Compatibility shim for Python 3.13+ (not needed if using 3.11)
render.yaml          → Render deployment blueprint
```

## How It Works

### Mention Responder (the main feature)
1. Polls X API every 15 seconds for new @ragetrack mentions
2. For each mention, checks if it's a reply to another tweet
3. Fetches the parent tweet text
4. Sends it to Claude Haiku with the ragebait knowledge base + scoring rubric
5. Posts the rating as a reply
6. Skips self-mentions (prevents infinite loop of rating its own tweets)
7. Saves last processed mention ID to `.last_mention_id` file for persistence

### Daily Scanner
1. Runs at 9:00 UTC daily (configurable)
2. Searches X using 11 queries targeting ragebait language patterns
3. Also scans 17 watchlisted accounts for their highest-engagement tweets
4. Filters by engagement score (min 100) and AI ragebait rating (min 5/10)
5. Posts a thread: intro → link to tweet (embed) → rating → link → rating → closer

## Known Issues to Fix

1. **Render deployment** — needs PYTHON_VERSION=3.11.0 and all env vars set. Redeploy after fixing.

2. **Tweet truncation** — AI responses sometimes exceed tweet character limits. Current fix: max_tokens=60, hard truncate to 140 chars. May need further tuning.

3. **Daily thread format** — the link+rating split into two tweets is clunky. Jack prefers to do daily threads manually for now. The mention responder is the priority.

4. **403 "not permitted" errors** — means X API write permissions aren't set up. Regenerate Access Token after enabling Read+Write in User Authentication settings.

5. **402 "no credits" errors** — X API credits ran out. Buy more at developer.x.com → Billing → Credits.

## How to Test Locally

```bash
git clone https://github.com/jbrew21/project-x.git
cd project-x
git checkout claude/ragebait-tracker-bot-zUwb5
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Create .env with all the keys above
python3 main.py
```

Then tag @ragetrack on any tweet from another account and it should reply within 15-30 seconds.

## Priority

1. **Get Render deploy working** so the bot runs 24/7 without Jack's Mac
2. **Verify mention responder works** on Render (tag @ragetrack, get a reply)
3. **Daily thread can wait** — Jack is doing those manually for now

## X Developer Portal Access

App name: TrackerRag8
App ID: 2039500170031714304
Bot account: @ragetrack
Developer portal: developer.x.com

Jack has the login credentials. He'll need to share them or add you to the project.
