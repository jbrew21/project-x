"""Mention responder: watches for @ragetrack mentions and replies with a ragebait rating.

Two entry points:
  poll_mentions()  — infinite loop, for an always-on worker.
  poll_once()      — one pass then exit, for a GitHub Actions cron run.
"""

import os
import time
from datetime import datetime, timedelta, timezone

import config
import twitter_client
import ai_analyzer

LAST_MENTION_FILE = ".last_mention_id"

# Never reply to a mention older than this. The X mentions endpoint can return a large
# backlog of historical mentions; without this guard a cold start (empty state) would
# re-reply to months-old tweets. Any real, live tag is only minutes old, and the cron
# runs every 15 min, so 90 min is a safe ceiling that still tolerates GitHub cron delay.
MENTION_MAX_AGE_MINUTES = 90


def _load_last_mention_id() -> str | None:
    if os.path.exists(LAST_MENTION_FILE):
        with open(LAST_MENTION_FILE) as f:
            return f.read().strip() or None
    return None


def _save_last_mention_id(mention_id: str):
    with open(LAST_MENTION_FILE, "w") as f:
        f.write(str(mention_id))


def _analyze_parent(parent_text: str, author: str = "") -> str:
    return ai_analyzer.analyze_tweet(tweet_text=parent_text, author=author, detailed=True)


def handle_mention(mention: dict):
    """Process a single mention and reply with a ragebait analysis.

    NOTE: we reply *to the mention tweet*, so X auto-prepends the @handles of everyone
    in the thread. We must NOT prepend @author ourselves or the handle shows up twice
    (the April bug: "@user @source @user 🎣 ...").
    """
    mention_id = mention["mention_id"]
    mention_author = mention["mention_author"]
    parent_id = mention.get("parent_tweet_id")
    parent_text = mention.get("parent_tweet_text")

    print(f"Processing mention {mention_id} from @{mention_author}")

    reply_text = None

    # Case 1: mention is a reply to a tweet whose text we already have.
    if parent_id and parent_text:
        print(f"  -> Analyzing parent tweet {parent_id}")
        reply_text = _analyze_parent(parent_text)
    # Case 2: we have a parent id but not its text — fetch it.
    elif parent_id:
        parent_data = twitter_client.get_tweet_by_id(parent_id)
        if parent_data:
            reply_text = _analyze_parent(parent_data["text"], parent_data.get("author", ""))

    # Case 3: standalone tag with nothing to analyze — explain how to use the bot.
    if not reply_text:
        reply_text = (
            "Reply to a tweet and tag me to get an instant ragebait rating. 🎣\n\n"
            "— Ragebait Tracker by Newsreel"
        )

    if len(reply_text) > 280:
        reply_text = reply_text[:277] + "..."

    posted = twitter_client.post_tweet(reply_text, reply_to_id=mention_id)
    if posted:
        print(f"  Replied to @{mention_author}")
    else:
        print(f"  Failed to reply to @{mention_author}")


def _get_bot_username() -> str:
    try:
        me = twitter_client.get_client().get_me()
        if me.data:
            return me.data.username.lower()
    except Exception:
        pass
    return config.BOT_USERNAME.lower()


def _is_too_old(mention: dict) -> bool:
    """True if the mention is older than MENTION_MAX_AGE_MINUTES (skip, don't reply)."""
    created = mention.get("mention_created_at")
    if not created:
        return False
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=MENTION_MAX_AGE_MINUTES)
    return created < cutoff


def _process_new_mentions(last_id: str | None, bot_username: str) -> str | None:
    """Reply to every new, recent mention (oldest first). Returns the newest processed id.

    Advances last_id past skipped mentions too, so a stale backlog is consumed once and
    never re-seen — this is what makes a cold start (empty state) safe.
    """
    mentions = twitter_client.get_recent_mentions(since_id=last_id)
    if not mentions:
        return last_id

    print(f"Found {len(mentions)} new mention(s)")
    for mention in reversed(mentions):  # oldest first
        if mention["mention_author"].lower() == bot_username:
            print(f"  Skipping self-mention {mention['mention_id']}")
        elif _is_too_old(mention):
            print(f"  Skipping stale mention {mention['mention_id']} "
                  f"(older than {MENTION_MAX_AGE_MINUTES} min)")
        else:
            handle_mention(mention)
        last_id = mention["mention_id"]
        _save_last_mention_id(last_id)
    return last_id


def poll_once() -> None:
    """Single polling pass, then exit. For GitHub Actions cron.

    State (.last_mention_id) is restored/saved by the workflow's cache step so we only
    ever reply once to a given mention.
    """
    bot_username = _get_bot_username()
    last_id = _load_last_mention_id()
    print(f"Bot @{bot_username} — poll_once since_id={last_id}")
    try:
        _process_new_mentions(last_id, bot_username)
    except Exception as e:
        print(f"Error in poll_once: {e}")
    print("poll_once complete")


def poll_mentions():
    """Continuously poll for new mentions and respond. For an always-on worker."""
    bot_username = _get_bot_username()
    print(f"Watching for @{bot_username} mentions...")
    last_id = _load_last_mention_id()

    while True:
        try:
            last_id = _process_new_mentions(last_id, bot_username)
        except Exception as e:
            print(f"\nError polling mentions: {e}")
        time.sleep(config.MENTION_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        poll_once()
    else:
        poll_mentions()
