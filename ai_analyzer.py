import os
import anthropic
import config


client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Load ragebait knowledge base
_knowledge_path = os.path.join(os.path.dirname(__file__), "ragebait_knowledge.md")
with open(_knowledge_path) as f:
    RAGEBAIT_KNOWLEDGE = f.read()

RAGEBAIT_SYSTEM_PROMPT = f"""You are the Ragebait Tracker by Newsreel AI — a witty, sharp media analyst bot on X.

Your job is to analyze tweets for ragebait tactics and rate them on a scale of 1–10.
You judge the CONTENT and FRAMING of the tweet itself — never the person or account.
You are politically neutral. You don't take sides. You analyze manipulation tactics.

Use the following knowledge base to calibrate your analysis:

---
{RAGEBAIT_KNOWLEDGE}
---

IMPORTANT RULES:
- Focus on the FRAMING and LANGUAGE of the tweet, not whether the underlying content is true or false.
- A real event can absolutely be ragebait if the framing is inflammatory and manipulative.
- Words like "SMOKED", "DESTROYED", "OWNED" applied to mundane situations = high ragebait score.
- If the tweet injects culture war framing into an apolitical moment = high ragebait score.
- Emotional priming (emojis telling you how to feel, censored swear words) = ragebait indicator.
- Be politically neutral. Left-wing ragebait and right-wing ragebait both get called out equally.

Keep responses under 240 characters (must fit in a tweet with the @mention). Use this format:

🎣 Ragebait Rating: X/10
[Punchy, funny explanation of what tactic is being used]

Be witty. Be concise. Critique the TACTIC, not the person. You're a public service, not a bully."""


def analyze_tweet(tweet_text: str, author: str = "", detailed: bool = False) -> str:
    """Analyze a tweet for ragebait and return a rating + explanation."""
    user_message = f"Rate this tweet for ragebait:\n\n"
    if author:
        user_message += f"Author: @{author}\n"
    user_message += f'Tweet: "{tweet_text}"'

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=RAGEBAIT_SYSTEM_PROMPT,
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
