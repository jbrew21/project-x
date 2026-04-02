"""
Ragebait Tracker by Newsreel AI
================================
An automated X bot that:
  1. Daily: Scans watchlisted accounts and rates their spiciest tweets
  2. 24/7: Responds to anyone who tags @ragebaittracker on a tweet

Usage:
  python main.py          — Run both daily scanner + mention responder
  python main.py scan     — Run one-time daily scan only
  python main.py watch    — Run mention responder only
"""

import sys
import threading

import schedule
import time

import config
from daily_scanner import post_daily_ratings
from mention_responder import poll_mentions


def run_scheduler():
    """Run the daily scan on a schedule."""
    scheduled_time = f"{config.DAILY_SCAN_HOUR:02d}:{config.DAILY_SCAN_MINUTE:02d}"
    schedule.every().day.at(scheduled_time).do(post_daily_ratings)
    print(f"📅 Daily scan scheduled for {scheduled_time} UTC")

    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print("=" * 50)
    print("🎣 RAGEBAIT TRACKER by Newsreel AI")
    print("=" * 50)

    if mode == "scan":
        print("Running one-time daily scan...")
        post_daily_ratings()

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
