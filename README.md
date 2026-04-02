# Ragebait Tracker by Newsreel AI

An automated X (Twitter) bot that detects and rates ragebait tweets on a scale of 1-10 using AI analysis.

## What It Does

### 1. Daily Ragebait Scan
Every day, the bot scans a watchlist of known ragebait accounts, pulls their highest-engagement tweets, and posts AI-generated ragebait ratings with funny, punchy explanations.

### 2. On-Demand Analysis
Anyone on X can reply to any tweet, tag `@ragebaittracker`, and ask "is this ragebait?" — the bot responds immediately with a ragebait rating and breakdown.

## Example Output

```
🎣 Ragebait Rating: 8/10
Classic engagement farming — vague enough to make everyone argue, specific enough to make everyone mad. Chef's kiss of manipulation.

📡 @some_account • Tracked by @ragebaittracker
```

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/jbrew21/project-x.git
cd project-x
pip install -r requirements.txt
```

### 2. Configure API keys

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

You'll need:
- **X/Twitter API keys** — Apply at [developer.x.com](https://developer.x.com). You need a project with **read and write** permissions (Free tier works for basic usage).
- **Anthropic API key** — Get one at [console.anthropic.com](https://console.anthropic.com). Pay-per-use pricing (very cheap for short tweet analyses).

### 3. Add accounts to the watchlist

Edit `config.py` and add X usernames to `WATCHLIST`:

```python
WATCHLIST = [
    "account_one",
    "account_two",
]
```

### 4. Run the bot

```bash
# Run everything (daily scan + mention responder)
python main.py

# Run a one-time scan only
python main.py scan

# Run the mention responder only
python main.py watch
```

## Architecture

```
main.py              — Entry point, runs scheduler + mention responder
ai_analyzer.py       — Claude API integration for ragebait scoring
twitter_client.py    — X API v2 client (tweepy) for reading/posting
daily_scanner.py     — Daily watchlist scanner and rater
mention_responder.py — Polls for @mentions and replies with analysis
config.py            — Configuration and environment variables
```

## Cost

- **X API**: Free tier supports reading tweets and posting (rate-limited)
- **Claude API**: ~$0.01-0.05 per tweet analysis (Sonnet model). A typical day costs pennies.

## Deployment

For always-on operation, deploy to any server or cloud platform:

```bash
# Using screen/tmux
screen -S ragebait
python main.py

# Or with systemd, Docker, Railway, Render, etc.
```

---

Built by [Newsreel AI](https://x.com/ragebaittracker)
