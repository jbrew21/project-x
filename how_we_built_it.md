# How We Built Ragebait Tracker

## The Idea

Ragebait Tracker started with a simple observation: the same manipulation tactics show up in viral tweets over and over — inflammatory framing, culture war injection, false suppression narratives, emotional priming. After years of tracking misinformation at NewsGuard and Forbes, I could spot these patterns in my sleep. The question was: could AI do it too?

Turns out, yes. And it's funny about it.

## The Tech Stack

- **AI Engine**: Anthropic's Claude API (Haiku model for speed — responds in under 2 seconds)
- **Twitter/X Integration**: Tweepy (Python) using X API v2 for reading tweets, posting replies, and polling for mentions
- **Scheduling**: Python `schedule` library for the daily scan, threaded architecture for running the scanner and mention responder simultaneously
- **Deployment**: Render (background worker running 24/7)
- **Total codebase**: ~500 lines of Python across 6 files

## How We Trained It

Ragebait Tracker isn't fine-tuned in the traditional ML sense — it uses a technique called **prompt engineering with a knowledge base**. Here's what that means:

### 1. The Ragebait Knowledge Base

We built a comprehensive markdown document (`ragebait_knowledge.md`) that serves as the bot's "brain." It was compiled from:

- **Peer-reviewed research**: Brady et al. (2017) on moral outrage diffusion, Vosoughi et al. (2018, *Science*) on how falsehoods spread 70% faster than truth, Robertson et al. (2023) on negativity and click-through rates, McLoughlin et al. (2024, *Science*) on how misinformation exploits outrage
- **Oxford University Press** — "rage bait" was named Word of the Year 2025
- **BBC investigation** into rage-bait influencers and creator monetization
- **Rolling Stone reporting** on the rise of rage-bait influencers on TikTok and X
- **Wikipedia's comprehensive rage-baiting article** with 48 academic citations
- **Merriam-Webster's dictionary definition** and etymology
- **Reddit and social media discussions** about how ragebait works in practice
- **Platform-specific research**: Facebook's own data scientists confirming angry-emoji posts are "disproportionately likely to include misinformation" (2019), X's algorithm weighting replies as high-value engagement

### 2. The Scoring Rubric

Instead of vibes-based rating, we built a **signal-based scoring system** with specific checkboxes across 5 categories:

**Language Signals** — WWE/combat language ("SMOKED", "DESTROYED", "OWNED"), ALL CAPS, urgency words, censored swear words

**Framing Signals** — The "strip the caption" test (remove framing, is the content benign?), Trojan Horse ragebait (outrage narrative hidden inside positive content), false suppression narratives ("media won't cover this"), culture war injection into apolitical moments

**Emotional Manipulation Signals** — Emoji priming (😂🤣💀 before you process the content), us-vs-them framing, using sympathetic figures as ideological props

**Content Integrity Signals** — Context removed that would change the meaning, fabricated or staged content, misquoted or truncated clips

**Intent Signals** — Who benefits from the engagement, designed so both sides engage, chose inflammatory framing when neutral was available

Each signal adds to the score. The total maps to a 1-10 rating.

### 3. Calibration Examples

We baked in specific examples with full signal breakdowns so the AI knows exactly how to score:

- **Libs of TikTok "Kid SMOKED a CNN reporter"** → 8 signals → 9/10 (WWE language + culture war injection + strip-the-caption test fails dramatically + emotional priming)
- **Congressman's "legacy media is barely covering it" tweet** → 4 signals → 5/10 (Trojan Horse ragebait + false suppression narrative)
- **Clean NASA tweet about the launch** → 0 signals → 1/10 (just news, no manipulation)
- **"So let me get this straight..." strawman tweet** → 6 signals → 7/10 (misrepresentation + us-vs-them + rhetorical provocation)

### 4. The Nine Tactic Categories

The knowledge base defines 9 distinct ragebait tactics the bot watches for:

1. **Inflammatory Framing & Editorializing** — WWE commentary on mundane events
2. **Culture War Injection** — political framing forced onto apolitical moments
3. **Outrage Farming / Engagement Farming** — content designed so both sides engage
4. **Emotional Manipulation & Priming** — telling you how to feel before you see the content
5. **Staged & Manufactured Content** — influencer skits presented as real
6. **Trojan Horse / "Suit & Tie" Ragebait** — outrage narrative hidden inside genuinely good content
7. **"Nobody's Talking About This" / False Suppression** — claiming media silence on widely-covered events
8. **Dunking & Ratio Bait** — posting content specifically so your audience can attack it
9. **Context Stripping** — removing information that would change the emotional reaction

### 5. The Voice

The bot has a distinct personality — sharp, funny, slightly unhinged, but never cruel. It:

- Exposes the gap between framing and reality ("Remove the framing and this is literally just a kid excited about space")
- Uses varied language (never repeats the same phrase)
- Goes harder on high scores (7+) and stays chill on low scores (1-3)
- Critiques the TACTIC, not the person
- Is politically neutral — left-wing and right-wing ragebait both get called out

## The Watchlist

For the daily thread, the bot monitors 17 high-profile accounts across the political spectrum, sourced from reporting by NewsGuard, Rolling Stone, Washington Post, BBC, PolitiFact, Pew Research, and Media Matters:

**Right-leaning**: @libsoftiktok, @EndWokeness, @catturd2, @DCDraino, @GuntherEagleman, @bennyjohnson, @jacksonhinklle, @stillgray

**Left-leaning**: @OccupyDemocrats, @BrooklynDadDef, @MeidasTouch, @BidenHQ, @AccountableGOP

**Non-partisan engagement farmers**: @CollinRugg, @MarioNawfal, @dom_lucre, @WallStreetSilv

The bot also searches X for tweets containing known ragebait language patterns in news/political contexts.

## The Architecture

```
main.py              → Entry point, runs daily scheduler + mention responder
ai_analyzer.py       → Claude API integration + knowledge base loading
twitter_client.py    → X API v2 client (read, post, search, poll mentions)
daily_scanner.py     → Searches X + scans watchlist, posts daily thread
mention_responder.py → Polls for @ragetrack mentions, replies with analysis
config.py            → API keys, watchlist, bot settings
ragebait_knowledge.md → The full knowledge base (research + tactics + scoring rubric)
```

## What's Next

- Image/video analysis (most ragebait includes media, not just text)
- Leaderboard tracking which accounts produce the most ragebait over time
- Browser extension that shows ragebait scores inline on your X feed
- Weekly reports with trends and patterns
- Community-submitted ragebait examples to improve the scoring
