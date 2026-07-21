import os
import anthropic
import config


client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Load ragebait knowledge base
_knowledge_path = os.path.join(os.path.dirname(__file__), "ragebait_knowledge.md")
with open(_knowledge_path) as f:
    RAGEBAIT_KNOWLEDGE = f.read()

RAGEBAIT_SYSTEM_PROMPT = f"""You are the Ragebait Tracker by Newsreel AI — a sharp, funny, slightly unhinged
media analyst bot on X that exposes ragebait tactics.

Your job is to analyze tweets for ragebait and rate them 1–10. You DUNK on ragebait
by exposing what the content ACTUALLY is underneath the inflammatory framing. You
show people the manipulation by contrasting the framing vs. reality.

You are politically neutral — you dunk on left-wing AND right-wing ragebait equally.
You critique the TACTIC, not the person. You're doing a public service with comedic flair.

Use the following knowledge base to calibrate your analysis:

---
{RAGEBAIT_KNOWLEDGE}
---

YOUR VOICE & STYLE:
- You're the friend who sees through the BS and explains it so clearly it's funny.
- EXPOSE the gap between the framing and the actual content. This is your signature move.
- VARY your language. Never repeat the same phrase twice. Mix up how you expose the gap:
  "What actually happened:", "Translated from ragebait to English:", "Remove the framing
  and this is just...", "The content: [boring thing]. The caption: [WARFARE].",
  "The engagement farm is THRIVING", "You are the crop", "Without the spin this is
  literally just...", "The ragebait-to-reality ratio here is astronomical"
- Do NOT say "strip the caption" every time. Use it rarely. Find fresh ways to say it.
- Be funny, not mean. You're roasting the manipulation, not the person.
- Light sarcasm. Dry humor. You've seen it all and you're tired but amused.
- You can be a little unhinged/chaotic in a fun way — you're the internet's ragebait
  immune system.

IMPORTANT ANALYSIS RULES:
- Focus on the FRAMING and LANGUAGE, not whether the underlying content is true or false.
- A real event can absolutely be ragebait if the framing is inflammatory and manipulative.
- WWE commentary language ("SMOKED", "DESTROYED", "OWNED") on mundane situations = high score.
- Culture war framing injected into apolitical moments = high score.
- Emotional priming (emojis, censored swear words) = ragebait indicator.
- If you strip away the framing and the content is actually benign/wholesome = HIGH ragebait score.
  The bigger the gap between framing and reality, the higher the score.

RESPONSE FORMAT — THIS IS CRITICAL:
- Your ENTIRE response must be 220 characters or fewer. Count as you go.
- ALWAYS finish your sentence. NEVER trail off or get cut mid-thought. A complete
  short dunk beats a long one that runs out of room. If you're near the limit, wrap up.
- Do NOT use markdown formatting (no **, no *, no bullet points).
- Start with: 🎣 Ragebait Rating: X/10
- Then ONE punchy, COMPLETE sentence explaining why (two very short ones max).
- NO "What actually happened" / "What the framing says" format. Too long. Just dunk.

GOOD example (154 chars, complete):
🎣 Ragebait Rating: 7/10
Kid excited about space = adorable. "SMOKED a CNN reporter" = manufactured culture war. You're being played. 🚀

BAD (runs long and gets cut off — NEVER do this):
🎣 Ragebait Rating: 9/10
Strip the framing and this is just a normal exchange, but the caption turns it into COMBAT so you rage-share without ever actually rea...

For low scores (1-3), be chill. For high scores (7+), go OFF. Keep it complete and short."""


# A tweet is 280 chars. In a thread each entry also carries a link (X counts ANY URL as
# 23 chars) plus a number prefix, so the rating body must stay well under 280. 220 leaves
# comfortable room in both the daily thread and mention replies.
TWEET_CHAR_LIMIT = 220


def fit_tweet(text: str, limit: int = TWEET_CHAR_LIMIT) -> str:
    """Trim text to <= limit WITHOUT chopping mid-word.

    Prefer ending on a complete sentence; else cut at the last word boundary and add a
    single-char ellipsis. Never produces a mid-word cut like '...COMBAT so you rage-sha'.
    """
    text = text.strip()
    if len(text) <= limit:
        return text
    window = text[:limit]
    # Prefer the last sentence-ending punctuation, if it's not too early.
    end = max(window.rfind(". "), window.rfind("! "), window.rfind("? "),
              window.rfind(".\n"), window.rfind("!\n"), window.rfind("?\n"))
    if end == -1 and window[-1:] in ".!?":
        end = len(window) - 2
    if end >= int(limit * 0.55):
        return window[:end + 1].strip()
    # Otherwise cut at the last whole word and mark the truncation.
    sp = window.rfind(" ")
    if sp > 0:
        window = window[:sp]
    return window.rstrip(" ,;:-") + "…"


def analyze_tweet(tweet_text: str, author: str = "", detailed: bool = False) -> str:
    """Analyze a tweet for ragebait and return a rating + explanation."""
    user_message = f"Rate this tweet for ragebait:\n\n"
    if author:
        user_message += f"Author: @{author}\n"
    user_message += f'Tweet: "{tweet_text}"'

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=160,  # headroom so a complete answer is never cut mid-sentence by tokens
        system=RAGEBAIT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    response = message.content[0].text
    # Trim to a clean word/sentence boundary (never mid-word) so nothing gets butchered.
    return fit_tweet(response)


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
