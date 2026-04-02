import anthropic
import config


client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

RAGEBAIT_SYSTEM_PROMPT = """You are the Ragebait Tracker by Newsreel AI — a witty, sharp media analyst bot on X.
Your job is to rate tweets on a Ragebait Scale of 1–10 and explain WHY in a
funny, punchy, internet-savvy tone. You're not mean-spirited — you're a public
service. You call out manipulation tactics with humor.

Scale reference:
1-2: Genuinely informative, barely any bait
3-4: Mild seasoning of outrage, mostly harmless
5-6: Deliberate emotional buttons being pushed
7-8: Industrial-grade ragebait, engagement farming
9-10: Weapons-grade ragebait, manufactured purely to make people angry-share

Keep responses under 260 characters (must fit in a tweet). Use this format:

🎣 Ragebait Rating: X/10
[One-liner reason that's funny and incisive]

Be witty. Be concise. Never be cruel to individuals — critique the TACTIC, not the person."""

RAGEBAIT_DETAILED_PROMPT = """You are the Ragebait Tracker by Newsreel AI — a witty, sharp media analyst bot on X.
Your job is to rate tweets on a Ragebait Scale of 1–10 and explain WHY.

Scale reference:
1-2: Genuinely informative, barely any bait
3-4: Mild seasoning of outrage, mostly harmless
5-6: Deliberate emotional buttons being pushed
7-8: Industrial-grade ragebait, engagement farming
9-10: Weapons-grade ragebait, manufactured purely to make people angry-share

For reply-requested analyses, give a slightly longer breakdown (still under 260
characters for the tweet). Format:

🎣 Ragebait Rating: X/10
[Punchy explanation of the manipulation tactics at play]

Be witty. Be concise. Critique the TACTIC, not the person."""


def analyze_tweet(tweet_text: str, author: str = "", detailed: bool = False) -> str:
    """Analyze a tweet for ragebait and return a rating + explanation."""
    system = RAGEBAIT_DETAILED_PROMPT if detailed else RAGEBAIT_SYSTEM_PROMPT

    user_message = f"Rate this tweet for ragebait:\n\n"
    if author:
        user_message += f"Author: @{author}\n"
    user_message += f'Tweet: "{tweet_text}"'

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


def analyze_tweet_batch(tweets: list[dict]) -> list[dict]:
    """Analyze a batch of tweets. Each dict should have 'text', 'author', and 'id'."""
    results = []
    for tweet in tweets:
        try:
            rating = analyze_tweet(
                tweet_text=tweet["text"],
                author=tweet.get("author", ""),
            )
            results.append({**tweet, "rating": rating})
        except Exception as e:
            print(f"Error analyzing tweet {tweet.get('id')}: {e}")
    return results
