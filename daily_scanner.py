"""Daily scanner: pulls recent tweets from watchlisted accounts, rates them,
and posts a daily Top 5 Ragebait thread every morning."""

import config
import twitter_client
import ai_analyzer


def scan_watchlist() -> list[dict]:
    """Scan all watchlisted accounts for their hottest recent tweets and rate them."""
    if not config.WATCHLIST:
        print("⚠️  Watchlist is empty — add accounts to config.WATCHLIST")
        return []

    all_tweets = []
    for username in config.WATCHLIST:
        print(f"Scanning @{username}...")
        tweets = twitter_client.get_recent_tweets_from_user(username, max_results=10)
        all_tweets.extend(tweets)

    if not all_tweets:
        print("No tweets found from watchlist.")
        return []

    # Sort by engagement (likes + retweets + replies) to find the spiciest ones
    def engagement_score(tweet):
        m = tweet.get("metrics", {})
        return (m.get("like_count", 0)
                + m.get("retweet_count", 0) * 2
                + m.get("reply_count", 0) * 3)

    all_tweets.sort(key=engagement_score, reverse=True)

    # Take the top 5 most engaged tweets across all watchlisted accounts
    top_tweets = all_tweets[:5]

    print(f"Analyzing top {len(top_tweets)} tweets...")
    rated = ai_analyzer.analyze_tweet_batch(top_tweets)

    return rated


def post_daily_thread():
    """Run the daily scan and post a threaded Top 5 Ragebait roundup."""
    rated_tweets = scan_watchlist()

    if not rated_tweets:
        print("Nothing to post today.")
        return

    # Tweet 1: The thread header
    header = (
        "🎣 DAILY RAGEBAIT REPORT 🎣\n\n"
        "Good morning. Here are yesterday's top 5 most egregious "
        "ragebait tweets, rated and roasted.\n\n"
        "A thread 🧵👇\n\n"
        "— Ragebait Tracker by Newsreel AI"
    )

    header_id = twitter_client.post_tweet(header)
    if not header_id:
        print("Failed to post thread header.")
        return
    print("✅ Posted thread header")

    # Tweets 2-6: Each rated tweet as a reply in the thread
    previous_id = header_id
    for i, tweet in enumerate(rated_tweets, 1):
        author = tweet.get("author", "unknown")
        rating_text = tweet["rating"]

        post_text = f"{i}/5\n\n@{author}:\n\"{tweet['text'][:80]}...\"\n\n{rating_text}"

        # Truncate if over 280 chars
        if len(post_text) > 280:
            post_text = post_text[:277] + "..."

        new_id = twitter_client.post_tweet(post_text, reply_to_id=previous_id)
        if new_id:
            previous_id = new_id
            print(f"✅ Posted {i}/5 — @{author}")
        else:
            print(f"❌ Failed to post {i}/5 — @{author}")

    # Final tweet: the closer
    closer = (
        "That's today's report. 🎣\n\n"
        "See ragebait in the wild? Reply to any tweet and "
        "tag @ragetrack — we'll rate it instantly.\n\n"
        "Stay aware. Don't be the crop. 🌾\n\n"
        "— Ragebait Tracker by Newsreel AI"
    )

    twitter_client.post_tweet(closer, reply_to_id=previous_id)
    print("✅ Posted thread closer")


if __name__ == "__main__":
    post_daily_thread()
