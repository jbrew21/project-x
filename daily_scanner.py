"""Daily scanner: pulls recent tweets from watchlisted accounts and rates them."""

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
        tweets = twitter_client.get_recent_tweets_from_user(username, max_results=5)
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


def post_daily_ratings():
    """Run the daily scan and post ratings as tweets."""
    rated_tweets = scan_watchlist()

    if not rated_tweets:
        print("Nothing to post today.")
        return

    for tweet in rated_tweets:
        # Build the tweet text with a quote-tweet style reference
        author = tweet.get("author", "unknown")
        rating_text = tweet["rating"]

        post_text = f"{rating_text}\n\n📡 @{author} • Tracked by @{config.BOT_USERNAME}"

        # Truncate if over 280 chars
        if len(post_text) > 280:
            post_text = post_text[:277] + "..."

        twitter_client.post_tweet(post_text)
        print(f"✅ Posted rating for @{author}")


if __name__ == "__main__":
    post_daily_ratings()
