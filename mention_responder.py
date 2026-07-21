"""Mention responder: watches for @ragetrack mentions and replies with a ragebait rating.

Two entry points:
  poll_mentions()  — infinite loop, for an always-on worker.
  poll_once()      — one pass then exit, for a GitHub Actions cron run.
"""

import os
import time

import config
import twitter_client
import ai_analyzer

LAST_MENTION_FILE = ".last_mention_id"


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


def _process_new_mentions(last_id: str | None, bot_username: str) -> str | None:
    """Reply to every new mention (oldest first). Returns the newest processed id."""
    mentions = twitter_client.get_recent_mentions(since_id=last_id)
    if not mentions:
        return last_id

    print(f"Found {len(mentions)} new mention(s)")
    for mention in reversed(mentions):  # oldest first
        if mention["mention_author"].lower() == bot_username:
            print(f"  Skipping self-mention {mention['mention_id']}")
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
