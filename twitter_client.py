import tweepy
import config


def get_client() -> tweepy.Client:
    """Get an authenticated X API v2 client."""
    return tweepy.Client(
        bearer_token=config.X_BEARER_TOKEN,
        consumer_key=config.X_API_KEY,
        consumer_secret=config.X_API_SECRET,
        access_token=config.X_ACCESS_TOKEN,
        access_token_secret=config.X_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True,
    )


def post_tweet(text: str, reply_to_id: str | None = None) -> str | None:
    """Post a tweet, optionally as a reply. Returns the new tweet ID."""
    client = get_client()
    try:
        response = client.create_tweet(
            text=text,
            in_reply_to_tweet_id=reply_to_id,
        )
        tweet_id = response.data["id"]
        print(f"Posted tweet {tweet_id}")
        return tweet_id
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None


def get_tweet_by_id(tweet_id: str) -> dict | None:
    """Fetch a tweet's text and author by ID."""
    client = get_client()
    try:
        response = client.get_tweet(
            tweet_id,
            tweet_fields=["text", "author_id", "created_at"],
            expansions=["author_id"],
            user_fields=["username"],
        )
        if not response.data:
            return None

        author_username = ""
        if response.includes and "users" in response.includes:
            author_username = response.includes["users"][0].username

        return {
            "id": str(response.data.id),
            "text": response.data.text,
            "author": author_username,
        }
    except Exception as e:
        print(f"Error fetching tweet {tweet_id}: {e}")
        return None


def get_recent_mentions(since_id: str | None = None) -> list[dict]:
    """Get recent mentions of the bot account."""
    client = get_client()
    try:
        me = client.get_me()
        if not me.data:
            print("Error: Could not fetch bot user info")
            return []

        response = client.get_users_mentions(
            me.data.id,
            since_id=since_id,
            tweet_fields=["text", "author_id", "created_at", "conversation_id",
                          "in_reply_to_user_id", "referenced_tweets"],
            expansions=["author_id", "referenced_tweets.id"],
            user_fields=["username"],
            max_results=20,
        )

        if not response.data:
            return []

        # Build a lookup of included tweets (the ones being replied to)
        referenced_tweets = {}
        if response.includes and "tweets" in response.includes:
            for t in response.includes["tweets"]:
                referenced_tweets[str(t.id)] = t.text

        # Build user lookup
        users = {}
        if response.includes and "users" in response.includes:
            for u in response.includes["users"]:
                users[str(u.id)] = u.username

        mentions = []
        for tweet in response.data:
            # Find the parent tweet this mention is replying to
            parent_tweet_id = None
            if tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.type == "replied_to":
                        parent_tweet_id = str(ref.id)
                        break

            mentions.append({
                "mention_id": str(tweet.id),
                "mention_text": tweet.text,
                "mention_author": users.get(str(tweet.author_id), ""),
                "parent_tweet_id": parent_tweet_id,
                "parent_tweet_text": referenced_tweets.get(parent_tweet_id, "")
                    if parent_tweet_id else None,
            })

        return mentions

    except Exception as e:
        print(f"Error fetching mentions: {e}")
        return []


def get_recent_tweets_from_user(username: str, max_results: int = 5) -> list[dict]:
    """Get recent tweets from a specific user."""
    client = get_client()
    try:
        user = client.get_user(username=username)
        if not user.data:
            return []

        response = client.get_users_tweets(
            user.data.id,
            max_results=max_results,
            tweet_fields=["text", "public_metrics", "created_at"],
            exclude=["retweets", "replies"],
        )

        if not response.data:
            return []

        return [
            {
                "id": str(t.id),
                "text": t.text,
                "author": username,
                "metrics": t.public_metrics,
            }
            for t in response.data
        ]

    except Exception as e:
        print(f"Error fetching tweets from @{username}: {e}")
        return []
