"""
Ragebait Tracker by Newsreel AI
================================
An automated X bot that:
  1. Daily: Scans watchlisted accounts and rates their spiciest tweets
  2. 24/7: Responds to anyone who tags @ragebaittracker on a tweet

Usage:
  python main.py                 — Run both daily scanner + mention responder (worker)
  python main.py scan            — Run one-time daily scan only (GitHub Actions cron)
  python main.py watch           — Run mention responder loop only (worker)
  python main.py mentions-once   — One mention-polling pass then exit (GitHub Actions cron)
  python main.py health          — Check auth + X API credit status, print READY/BLOCKED
"""

import sys
import threading

import schedule
import time

import config
from daily_scanner import post_daily_thread
from mention_responder import poll_mentions, poll_once


def health_check() -> bool:
    """Print a clear readiness report. Returns True if the bot can actually operate.

    Use after topping up the X API plan to confirm the credit wall is cleared:
        python main.py health
    """
    import twitter_client
    c = twitter_client.get_client()
    try:
        me = c.get_me()
        print(f"Auth OK — @{me.data.username}")
    except Exception as e:
        print(f"AUTH FAILED: {e}")
        return False
    try:
        r = c.search_recent_tweets(query="trump lang:en", max_results=10)
        n = len(r.data) if r.data else 0
        print(f"X API read OK — search returned {n} tweets")
        print("READY: credits available. Daily thread + mentions will run.")
        return True
    except Exception as e:
        if "402" in str(e):
            print("BLOCKED: X API credits depleted (402). Top up the plan in the "
                  "developer portal — nothing runs until then.")
        else:
            print(f"BLOCKED: {e}")
        return False


def run_scheduler():
    """Run the daily scan on a schedule."""
    scheduled_time = f"{config.DAILY_SCAN_HOUR:02d}:{config.DAILY_SCAN_MINUTE:02d}"
    schedule.every().day.at(scheduled_time).do(post_daily_thread)
    print(f"📅 Daily scan scheduled for {scheduled_time} UTC")

    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print("=" * 50)
    print("🎣 RAGEBAIT TRACKER by Newsreel AI")
    print("=" * 50)

    if mode == "health":
        ok = health_check()
        sys.exit(0 if ok else 1)

    elif mode == "scan":
        print("Running one-time daily scan...")
        post_daily_thread()

    elif mode == "mentions-once":
        print("Running one-time mention poll...")
        poll_once()

    elif mode == "watch":
        print("Starting mention responder...")
        poll_mentions()

    else:
        # Run both: scheduler in a background thread, mentions in foreground
        print("Starting full bot (daily scan + mention responder)...")
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        poll_mentions()


if __name__ == "__main__":
    main()
