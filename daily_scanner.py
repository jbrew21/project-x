"""Daily scanner for the @ragetrack "Daily Ragebait Report".

Strategy (fixes the "random foreign posts" problem):
  1. PRIMARY signal = the curated US watchlist (config.WATCHLIST) — recognizable
     left/right/non-partisan engagement-farm accounts. On-brand by construction.
  2. SUPPLEMENT = a recent-search sweep for ragebait language patterns, to catch
     viral offenders who aren't on the watchlist.
  3. Rate every candidate with the AI (ragebait_knowledge.md rubric), KEEP only
     genuine ragebait (score >= MIN_RAGEBAIT_SCORE), then post the 5 highest-rated.

This guarantees the daily thread is (a) actually ragebait, not random high-engagement
tweets, and (b) weighted toward the US culture-war accounts Newsreel's audience knows.
"""

from datetime import datetime, timedelta, timezone

import config
import twitter_client
import ai_analyzer


# Search queries designed to surface likely ragebait tweets with high engagement.
# These target common ragebait language patterns and inflammatory framing.
RAGEBAIT_SEARCH_QUERIES = [
    # WWE/inflammatory language applied to news/politics (not gaming/sports)
    '"DESTROYED" (media OR reporter OR liberal OR conservative OR Democrat OR Republican) -is:retweet -is:reply lang:en',
    '"SMOKED" (reporter OR CNN OR media OR interview OR Democrat OR Republican) -is:retweet -is:reply lang:en',
    '"SLAMMED" (media OR congress OR senator OR policy OR Biden OR Trump) -is:retweet -is:reply lang:en',
    # False suppression narratives
    '"media won\'t cover this" -is:retweet lang:en',
    '"nobody is talking about this" -is:retweet lang:en',
    '"why isn\'t anyone talking about" -is:retweet lang:en',
    # Outrage framing
    '"let that sink in" (politics OR media OR government) -is:retweet lang:en',
    '"this is insane" (policy OR media OR government OR woke) -is:retweet -is:reply lang:en',
    # Culture war bait
    '"clapped back" -is:retweet lang:en',
    '"gets DESTROYED" -is:retweet lang:en',
    '"absolutely WRECKED" -is:retweet lang:en',
]

# Minimum public engagement for a tweet to even be considered.
MIN_ENGAGEMENT_SCORE = 100
# Only tweets from roughly the last day count for a "last 24 hours" report.
# 36h of slack absorbs timezone / scan-timing drift without going stale.
RECENCY_HOURS = 36
# A tweet must score at least this on the 1-10 ragebait scale to make the thread.
MIN_RAGEBAIT_SCORE = 6
# How many candidates to send to the AI rater (bounds cost + rate limits).
MAX_WATCHLIST_CANDIDATES = 12
MAX_SEARCH_CANDIDATES = 8
# Cap tweets-per-account in the final thread so it reads as a balanced report,
# not a grudge against one account.
MAX_PER_AUTHOR = 2


def _engagement_score(tweet: dict) -> int:
    """Weight replies + quotes heavily — controversy is the ragebait signal."""
    m = tweet.get("metrics", {}) or {}
    return (m.get("like_count", 0)
            + m.get("retweet_count", 0) * 2
            + m.get("reply_count", 0) * 3
            + m.get("quote_count", 0) * 3)


def _is_recent(tweet: dict) -> bool:
    """True if the tweet was posted within RECENCY_HOURS. Missing date => keep."""
    created = tweet.get("created_at")
    if not created:
        return True
    if isinstance(created, str):
        try:
            created = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            return True
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created >= datetime.now(timezone.utc) - timedelta(hours=RECENCY_HOURS)


def _extract_rating(tweet: dict) -> int:
    """Pull the integer 1-10 score out of the AI 'rating' text."""
    text = tweet.get("rating", "") or ""
    for i in range(10, 0, -1):
        if f"{i}/10" in text:
            return i
    return 0


def gather_watchlist_candidates() -> list[dict]:
    """Recent, high-engagement tweets from the curated US watchlist. On-brand."""
    if not config.WATCHLIST:
        return []

    pool = []
    for username in config.WATCHLIST:
        print(f"Scanning @{username}...")
        tweets = twitter_client.get_recent_tweets_from_user(username, max_results=10)
        pool.extend(t for t in tweets if _is_recent(t))

    pool.sort(key=_engagement_score, reverse=True)
    candidates = pool[:MAX_WATCHLIST_CANDIDATES]
    print(f"Watchlist: {len(candidates)} recent candidates")
    return candidates


def gather_search_candidates() -> list[dict]:
    """Viral ragebait-language tweets from recent search. Catches non-watchlist offenders."""
    pool = []
    seen = set()
    for query in RAGEBAIT_SEARCH_QUERIES:
        print(f"Searching: {query[:50]}...")
        for tweet in twitter_client.search_viral_tweets(query, max_results=20):
            if tweet["id"] not in seen and _is_recent(tweet):
                seen.add(tweet["id"])
                pool.append(tweet)

    pool = [t for t in pool if _engagement_score(t) >= MIN_ENGAGEMENT_SCORE]
    pool.sort(key=_engagement_score, reverse=True)
    candidates = pool[:MAX_SEARCH_CANDIDATES]
    print(f"Search: {len(candidates)} viral candidates above threshold")
    return candidates


def find_daily_ragebait() -> list[dict]:
    """Gather from watchlist + search, AI-rate everything, keep the 5 worst offenders."""
    candidates = []
    seen = set()
    # Watchlist first so on-brand accounts win ties.
    for tweet in gather_watchlist_candidates() + gather_search_candidates():
        if tweet["id"] not in seen:
            seen.add(tweet["id"])
            candidates.append(tweet)

    if not candidates:
        print("No candidates found.")
        return []

    print(f"AI-rating {len(candidates)} candidates...")
    rated = ai_analyzer.analyze_tweet_batch(candidates)

    # Keep only genuine ragebait, then rank by score, breaking ties on engagement.
    rated = [t for t in rated if _extract_rating(t) >= MIN_RAGEBAIT_SCORE]
    rated.sort(key=lambda t: (_extract_rating(t), _engagement_score(t)), reverse=True)
    print(f"{len(rated)} tweets scored >= {MIN_RAGEBAIT_SCORE}/10")

    # Greedily pick the top 5 while capping tweets-per-account for a balanced thread.
    top, per_author = [], {}
    for tweet in rated:
        author = (tweet.get("author") or "").lower()
        if per_author.get(author, 0) >= MAX_PER_AUTHOR:
            continue
        per_author[author] = per_author.get(author, 0) + 1
        top.append(tweet)
        if len(top) == 5:
            break

    # If the cap left us short (few accounts had ragebait today), backfill by score.
    if len(top) < 5:
        chosen = {t["id"] for t in top}
        for tweet in rated:
            if tweet["id"] not in chosen:
                top.append(tweet)
                if len(top) == 5:
                    break

    return top


def post_daily_thread():
    """Run the daily scan and post a threaded Top 5 Ragebait roundup."""
    import time

    print("Searching X for today's worst ragebait...")
    rated_tweets = find_daily_ragebait()

    if not rated_tweets:
        print("Nothing scored as ragebait today. Not posting.")
        return

    count = len(rated_tweets)
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Tweet 1: Intro
    intro = (
        f"🎣 DAILY RAGEBAIT REPORT — {today}\n\n"
        f"I scanned the loudest accounts and most viral posts of the last 24 hours.\n\n"
        f"Here are the {count} worst ragebait offenders I found — "
        f"rated, roasted, and exposed. 🧵"
    )

    intro_id = twitter_client.post_tweet(intro)
    if not intro_id:
        print("Failed to post intro tweet.")
        return
    print("Posted intro tweet")
    time.sleep(2)

    # Tweets 2+: Each rated tweet as a reply in the thread
    previous_id = intro_id
    for i, tweet in enumerate(rated_tweets, 1):
        author = tweet.get("author", "unknown")
        tweet_id = tweet.get("id", "")
        rating_text = tweet["rating"]
        tweet_link = f"https://x.com/{author}/status/{tweet_id}"

        # X counts links as 23 chars. Number + newlines ~= 10 chars.
        max_rating_len = 240
        if len(rating_text) > max_rating_len:
            rating_text = rating_text[:max_rating_len - 3] + "..."

        post_text = f"{i}.\n\n{rating_text}\n\n{tweet_link}"

        if len(post_text) > 280:
            over = len(post_text) - 277
            rating_text = rating_text[:len(rating_text) - over - 3] + "..."
            post_text = f"{i}.\n\n{rating_text}\n\n{tweet_link}"

        new_id = twitter_client.post_tweet(post_text, reply_to_id=previous_id)
        if new_id:
            previous_id = new_id
            print(f"Posted {i}/{count} — @{author}")
        else:
            print(f"Failed to post {i}/{count} — @{author}")
        time.sleep(2)

    # Final tweet: CTA
    closer = (
        "That's today's report.\n\n"
        "See ragebait in the wild? Reply to any tweet and "
        "tag @ragetrack — I'll rate it instantly. 🎣\n\n"
        "Don't be the crop. 🌾"
    )
    twitter_client.post_tweet(closer, reply_to_id=previous_id)
    print("Posted closer")


if __name__ == "__main__":
    post_daily_thread()
