# Daily Briefing — The Self-Improving Loop

**This is the crown jewel of the setup.** A daily cron that doesn't just report
— it **makes the agent smarter over time** by reading real work and patching its
own skills.

## How it works

Runs every morning (e.g. 07:00). Three data-gathering steps:

1. **Telemetry collector** — a <1s script that gathers ground truth:
   `git log` last 24h per repo, dirty WIP, server status, tunnel status.
2. **Session search** — reads the last 1–2 days of actual sessions.
3. **Skill library scan** — lists what skills exist and could improve.

Then it produces a structured briefing:

```
☀️ DAILY BRIEFING — Selasa, 11 Agu

**KEMAREN**        # real work rekap (git + sessions)
• beresin bug CSS di skill-arena

**HARI INI**       # concrete next actions
• commit WIP, lanjut fitur X

**SARAN (AGENTIC + SELF-IMPROVING)**
• [P1] Task konkret hari ini — exact command, "tinggal bilang gas"
• [P2] Skill/knowledge upgrade — what the agent lacks
• [P3] Fix broken tooling (e.g. stale repo list)
```

## The self-improving part

The briefing is allowed to **act on its own suggestions** — it reads the skill
library, identifies gaps, and **patches skills directly** (via the skill tools).
This is a verified, real loop: e.g. a briefing has autonomously updated the cron
operations skill with the day's lessons and deduplicated overlapping sections.

This is what makes the agent "self-improving" in practice, not just marketing:
every day it reads what it did, figures out what it doesn't know, and encodes
that into its skill library for tomorrow.

## Key design decisions

- **Model pinning** — the job is pinned to a reliable provider (not the default
  that can change), so it doesn't silently fail on a flaky nightly model.
- **Fallback chain** — if the primary provider times out, it falls back. Never
  "silently didn't run."
- **Delivery** — results go to the owner's Telegram as a formatted briefing.
- **Honesty** — collects *real* data (`git log`, sessions), never imagines work.