"""Daily scanner: searches X for the most viral ragebait tweets in the last 24 hours
and posts a daily Top 5 thread every morning."""

import config
import twitter_client
import ai_analyzer


# Search queries designed to surface likely ragebait tweets with high engagement.
# These target common ragebait language patterns and inflammatory framing.
RAGEBAIT_SEARCH_QUERIES = [
    # WWE/inflammatory language applied to news/politics (not gaming/sports)
    '"DESTROYED" (media OR reporter OR liberal OR conservative) -is:retweet -is:reply lang:en',
    '"SMOKED" (reporter OR CNN OR media OR interview) -is:retweet -is:reply lang:en',
    '"SLAMMED" (media OR congress OR senator OR policy) -is:retweet -is:reply lang:en',
    # False suppression narratives
    '"media won\'t cover this" -is:retweet lang:en',
    '"nobody is talking about this" -is:retweet lang:en',
    '"why isn\'t anyone talking about" -is:retweet lang:en',
    # Outrage framing
    '"let that sink in" (politics OR media OR government) -is:retweet lang:en',
    '"this is insane" (policy OR media OR government OR woke) -is:retweet -is:reply lang:en',
    # Culture war bait
    '"clapped back at" -is:retweet lang:en',
    '"gets DESTROYED" -is:retweet lang:en',
    '"absolutely WRECKED" -is:retweet lang:en',
]

# Minimum engagement to be considered for the daily thread
MIN_ENGAGEMENT_SCORE = 100


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

    # Filter out low-engagement tweets, then sort
    all_tweets = [t for t in all_tweets if engagement_score(t) >= MIN_ENGAGEMENT_SCORE]
    all_tweets.sort(key=engagement_score, reverse=True)

    print(f"Found {len(all_tweets)} tweets above engagement threshold")

    if not all_tweets:
        print("No high-engagement tweets found.")
        return []

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

    # Only keep tweets that actually scored as ragebait (5+/10)
    rated = [t for t in rated if extract_rating(t) >= 5]
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
    import time

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

    count = len(rated_tweets)
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    # Tweet 1: Intro
    intro = (
        f"🎣 DAILY RAGEBAIT REPORT — {today}\n\n"
        f"I just scanned thousands of viral tweets from the last 24 hours.\n\n"
        f"Here are the {count} worst ragebait offenders I found — "
        f"rated, roasted, and exposed. 🧵"
    )

    intro_id = twitter_client.post_tweet(intro)
    if not intro_id:
        print("Failed to post intro tweet.")
        return
    print("✅ Posted intro tweet")
    time.sleep(2)

    # Tweets 2+: Each rated tweet as a reply in the thread
    previous_id = intro_id
    for i, tweet in enumerate(rated_tweets, 1):
        author = tweet.get("author", "unknown")
        tweet_id = tweet.get("id", "")
        rating_text = tweet["rating"]
        tweet_link = f"https://x.com/{author}/status/{tweet_id}"

        # Keep rating short enough that the link fits
        # Max tweet = 280 chars. Link = ~50 chars. Number + newlines = ~10 chars.
        max_rating_len = 280 - len(tweet_link) - 15
        if len(rating_text) > max_rating_len:
            rating_text = rating_text[:max_rating_len - 3] + "..."

        post_text = f"{i}.\n\n{rating_text}\n\n{tweet_link}"

        new_id = twitter_client.post_tweet(post_text, reply_to_id=previous_id)
        if new_id:
            previous_id = new_id
            print(f"✅ Posted {i}/{count} — @{author}")
        else:
            print(f"❌ Failed to post {i}/{count} — @{author}")

        time.sleep(2)

    # Final tweet: CTA
    closer = (
        "That's today's report.\n\n"
        "See ragebait in the wild? Reply to any tweet and "
        "tag @ragetrack — I'll rate it instantly. 🎣\n\n"
        "Don't be the crop. 🌾"
    )

    twitter_client.post_tweet(closer, reply_to_id=previous_id)
    print("✅ Posted closer")


if __name__ == "__main__":
    post_daily_thread()
