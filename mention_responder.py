"""Mention responder: watches for @ragebaittracker mentions and replies with analysis."""

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
        f.write(mention_id)


def handle_mention(mention: dict):
    """Process a single mention and reply with a ragebait analysis."""
    mention_id = mention["mention_id"]
    mention_author = mention["mention_author"]
    parent_id = mention.get("parent_tweet_id")
    parent_text = mention.get("parent_tweet_text")

    print(f"Processing mention {mention_id} from @{mention_author}")

    # If the mention is a reply to another tweet, analyze that parent tweet
    if parent_id and parent_text:
        print(f"  → Analyzing parent tweet {parent_id}")
        rating = ai_analyzer.analyze_tweet(
            tweet_text=parent_text,
            detailed=True,
        )
        reply_text = f"@{mention_author} {rating}"
    else:
        # The mention might contain a tweet URL or just be a standalone tag
        # Try to extract a tweet being referenced
        parent_data = None
        if parent_id and not parent_text:
            parent_data = twitter_client.get_tweet_by_id(parent_id)

        if parent_data:
            rating = ai_analyzer.analyze_tweet(
                tweet_text=parent_data["text"],
                author=parent_data.get("author", ""),
                detailed=True,
            )
            reply_text = f"@{mention_author} {rating}"
        else:
            reply_text = (
                f"@{mention_author} Reply to a tweet and tag me to get a "
                f"ragebait rating! 🎣\n\n"
                f"— Ragebait Tracker by Newsreel AI"
            )

    # Truncate to 280 chars
    if len(reply_text) > 280:
        reply_text = reply_text[:277] + "..."

    twitter_client.post_tweet(reply_text, reply_to_id=mention_id)
    print(f"  ✅ Replied to @{mention_author}")


def poll_mentions():
    """Continuously poll for new mentions and respond."""
    print(f"👀 Watching for @{config.BOT_USERNAME} mentions...")
    last_id = _load_last_mention_id()

    while True:
        try:
            mentions = twitter_client.get_recent_mentions(since_id=last_id)

            if mentions:
                print(f"Found {len(mentions)} new mention(s)")
                # Process oldest first
                for mention in reversed(mentions):
                    handle_mention(mention)
                    last_id = mention["mention_id"]
                    _save_last_mention_id(last_id)
            else:
                print(".", end="", flush=True)

        except Exception as e:
            print(f"\nError polling mentions: {e}")

        time.sleep(config.MENTION_POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    poll_mentions()
