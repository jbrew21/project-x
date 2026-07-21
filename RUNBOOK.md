# Ragebait Tracker (@ragetrack) — Operations Runbook

Last updated: 2026-07-21

## Current status

Code is complete and verified. **The only thing stopping live operation is the X API
account being out of credits** (`402 Payment Required — credits depleted`). This blocks
both reads (search, mention polling) and writes (posting). Nothing runs until the plan
is topped up.

Verify status any time:

```bash
cd ~/project-x
python main.py health      # prints "READY" or "BLOCKED: credits depleted"
```

## Unblock (only the account owner can do this)

1. X developer portal → the @ragetrack app → **top up / upgrade the API plan** so it has
   credits.
2. `python main.py health` → should now print `READY`.
3. Optional immediate test: `python main.py scan` posts a daily thread now;
   tag @ragetrack from another account to test a mention reply.

## How it runs (once credits exist)

Two GitHub Actions workflows in `.github/workflows/` (secrets already set on the repo):

| Workflow | Schedule | What it does |
|---|---|---|
| `daily-thread.yml` | 13:00 UTC (9am ET) daily | Scans the whole of X, posts the Top-5 ragebait thread |
| `mentions.yml` | every 10 min | Replies to anyone who tags @ragetrack |

Both fail *gracefully* while credits are down (they post nothing and exit clean), so the
schedules stay healthy and start working automatically the moment credits return.

## What it finds (methodology)

- Full rubric: `ragebait_knowledge.md` (signal checklist + 1–10 scoring + calibration).
- The daily scan searches **all of X** with US/English-anchored ragebait queries
  (primary), plus the curated watchlist in `config.py` as a capped supplement
  (≤2 of the 5 slots). Everything is AI-rated; only genuine ragebait (score ≥6/10)
  makes the thread, ranked worst-first, max 2 per account.

## Tuning knobs (balance responsiveness/coverage vs. X API credit burn)

The X plan is metered, so every search + poll costs credits. Adjust to the budget:

- **Mention poll frequency** — `.github/workflows/mentions.yml` cron:
  `*/5` snappiest (~288/day) · `*/10` default (144/day) · `*/30` frugal (48/day).
- **Daily scan breadth** — `RAGEBAIT_SEARCH_QUERIES` in `daily_scanner.py` (12 queries
  now; add more for wider coverage at higher credit cost) and `max_results` per query.
- **Quality bar** — `MIN_RAGEBAIT_SCORE` (6) and `MIN_ENGAGEMENT_SCORE` (250) in
  `daily_scanner.py`.

## Optional: responsive mentions via an always-on Render worker

GitHub's `schedule` trigger is unreliable/delayed — fine for the once-a-day thread, less
so for snappy mention replies. For near-real-time replies, run the worker instead:

1. Render → New → **Background Worker** → connect `jbrew21/project-x`.
2. Build: `pip install -r requirements.txt` · Start: `python main.py watch`
   (`render.yaml` already describes this).
3. Add the same env vars as the GitHub secrets (X keys + `ANTHROPIC_API_KEY`,
   `BOT_USERNAME=ragetrack`).
4. If you run the worker, disable `mentions.yml` (delete it or comment out its `schedule`)
   so the two don't double-reply.

Note: a worker polls continuously, so it burns more credits than the cron — size the X
plan accordingly.

## Command reference

```bash
python main.py health          # check auth + credit status
python main.py scan            # post one daily thread now
python main.py mentions-once   # one mention-poll pass (what the cron runs)
python main.py watch           # continuous mention responder (for the worker)
```
