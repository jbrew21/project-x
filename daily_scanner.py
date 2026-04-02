"""Daily scanner: searches X for the most viral ragebait tweets in the last 24 hours
and posts a daily Top 5 thread every morning."""

import config
import twitter_client
import ai_analyzer


# Search queries designed to surface likely ragebait tweets with high engagement.
# These target common ragebait language patterns and inflammatory framing.
RAGEBAIT_SEARCH_QUERIES = [
    # WWE/inflammatory language on news topics
    '"DESTROYED" -is:retweet lang:en min_faves:1000',
    '"SMOKED" -is:retweet lang:en min_faves:1000',
    '"OWNED" -is:retweet lang:en min_faves:500',
    '"SLAMMED" -is:retweet lang:en min_faves:1000',
    # False suppression narratives
    '"media won\'t cover" -is:retweet lang:en min_faves:500',
    '"nobody is talking about" -is:retweet lang:en min_faves:500',
    '"media doesn\'t want you" -is:retweet lang:en min_faves:500',
    # Outrage framing
    '"let that sink in" -is:retweet lang:en min_faves:1000',
    '"I can\'t believe" -is:retweet lang:en min_faves:1000',
    '"this is insane" -is:retweet lang:en min_faves:1000',
    # Culture war bait
    '"clapped back" -is:retweet lang:en min_faves:500',
    '"gets WRECKED" -is:retweet lang:en min_faves:500',
]


def scan_viral_ragebait() -> list[dict]:
    """Search X for the most viral likely-ragebait tweets from the last 24 hours."""
    all_tweets = []
    seen_ids = set()

    for query in RAGEBAIT_SEARCH_QUERIES:
        print(f"Searching: {query[:50]}...")
        results = twitter_client.search_viral_tweets(query, max_results=20)
        for tweet in results:
            if tweet["id"] not in seen_ids:
                seen_ids.add(tweet["id"])
                all_tweets.append(tweet)

    if not all_tweets:
        print("No viral tweets found.")
        return []

    # Sort by engagement — weight replies heavily (replies = controversy = ragebait signal)
    def engagement_score(tweet):
        m = tweet.get("metrics", {})
        return (m.get("like_count", 0)
                + m.get("retweet_count", 0) * 2
                + m.get("reply_count", 0) * 3
                + m.get("quote_count", 0) * 3)

    all_tweets.sort(key=engagement_score, reverse=True)

    # Take top 15 by engagement, then AI-rate them all and pick the 5 worst offenders
    candidates = all_tweets[:15]
    print(f"Analyzing top {len(candidates)} candidates...")
    rated = ai_analyzer.analyze_tweet_batch(candidates)

    # Parse the rating number from the AI response and sort by highest ragebait score
    def extract_rating(tweet):
        text = tweet.get("rating", "")
        for i in range(10, 0, -1):
            if f"{i}/10" in text:
                return i
        return 0

    rated.sort(key=extract_rating, reverse=True)

    # Return the top 5 highest-rated ragebait tweets
    return rated[:5]


def scan_watchlist() -> list[dict]:
    """Scan all watchlisted accounts for their hottest recent tweets and rate them."""
    if not config.WATCHLIST:
        return []

    all_tweets = []
    for username in config.WATCHLIST:
        print(f"Scanning @{username}...")
        tweets = twitter_client.get_recent_tweets_from_user(username, max_results=10)
        all_tweets.extend(tweets)

    if not all_tweets:
        return []

    def engagement_score(tweet):
        m = tweet.get("metrics", {})
        return (m.get("like_count", 0)
                + m.get("retweet_count", 0) * 2
                + m.get("reply_count", 0) * 3)

    all_tweets.sort(key=engagement_score, reverse=True)
    top_tweets = all_tweets[:5]

    print(f"Analyzing top {len(top_tweets)} watchlist tweets...")
    rated = ai_analyzer.analyze_tweet_batch(top_tweets)

    return rated


def post_daily_thread():
    """Run the daily scan and post a threaded Top 5 Ragebait roundup."""
    # Try viral search first, fall back to watchlist
    print("🔍 Searching X for today's worst ragebait...")
    rated_tweets = scan_viral_ragebait()

    # If search didn't return enough, supplement with watchlist
    if len(rated_tweets) < 5 and config.WATCHLIST:
        print("Supplementing with watchlist scan...")
        watchlist_rated = scan_watchlist()
        seen_ids = {t["id"] for t in rated_tweets}
        for tweet in watchlist_rated:
            if tweet["id"] not in seen_ids and len(rated_tweets) < 5:
                rated_tweets.append(tweet)

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

        # Truncate the original tweet text for the quote
        original_text = tweet["text"][:80]
        if len(tweet["text"]) > 80:
            original_text += "..."

        post_text = f"{i}/5\n\n@{author}:\n\"{original_text}\"\n\n{rating_text}"

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
